import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable

import google.genai as genai

from src.io.formats import (
    ProjectConfig,
    AppConfig,
    TranslationResult,
    ProviderType,
    OllamaConfig,
)
from src.core.api_manager import ApiKeyManager

logger = logging.getLogger(__name__)


class TranslationProvider(ABC):
    @abstractmethod
    def translate_batch(
        self,
        items: dict[str, str],
        prompt: str,
        config: ProjectConfig,
        on_progress: Optional[Callable] = None,
    ) -> TranslationResult:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def get_models(self) -> list[str]:
        ...


def _parse_json_response(text: str) -> dict[str, str]:

    if text == "None": return {}

    raw = text.strip()
    raw = re.sub(r"^```json\s*|```$", "", raw).strip()
    raw = raw.replace("`", "").strip()

    while raw[:1] != "{":
        raw = raw[1:]
        if not raw:
            raise ValueError("Response has no JSON object")

    while raw[-1:] != "}":
        raw = raw[:-1]
        if raw[-2:] != '",':
            raw = raw[:-1] + "}"
            break
        if not raw:
            raise ValueError("Response has no JSON object")

    while True:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Truncating malformed JSON tail...")
        while raw[-2:] != '",':
            raw = raw[:-1]
            if not raw:
                raise ValueError("Cannot parse JSON from response")
        raw = raw[:-1] + "}"


class GeminiProvider(TranslationProvider):
    def __init__(self, api_keys: list[str]):
        self._key_manager = ApiKeyManager(api_keys)

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return self._key_manager.key_count > 0

    def get_models(self) -> list[str]:
        return [
            "gemini-3.5-flash",
            "gemini-3.1-pro-preview",
            "gemini-3.1-flash-lite",
            "gemini-3.0-deep-think",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
        ]

    def translate_batch(
        self,
        items: dict[str, str],
        prompt: str,
        config: ProjectConfig,
        on_progress: Optional[Callable] = None,
    ) -> TranslationResult:
        max_retries = 3
        last_error: Optional[str] = None

        for attempt in range(max_retries):
            key = self._key_manager.next_key()
            logger.info(
                "Gemini attempt %d/%d with key index %d",
                attempt + 1,
                max_retries,
                self._key_manager._index - 1,
            )

            try:
                client = genai.Client(api_key=key)
                chat = client.chats.create(model=config.model)
                payload = f"{prompt}\n{json.dumps(items, indent=4)}"
                response = chat.send_message(payload)

                if not response.candidates or not response.candidates[0].content.parts:
                    raise RuntimeError("Empty response from Gemini")

                text = response.candidates[0].content.parts[0].text
                parsed = _parse_json_response(str(text))

                failed = [k for k in items if k not in parsed]
                if failed:
                    logger.warning("%d keys missing in Gemini response", len(failed))

                return TranslationResult(
                    success=True,
                    data=parsed,
                    failed_keys=failed,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning("Gemini attempt %d failed: %s", attempt + 1, last_error)
                self._key_manager.rotate()
                time.sleep(3)

        return TranslationResult(
            success=False,
            data={},
            failed_keys=list(items.keys()),
            error=f"All Gemini attempts failed: {last_error}",
        )


class OllamaProvider(TranslationProvider):
    def __init__(self, ollama_config: OllamaConfig):
        self.ollama_config = ollama_config

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        import urllib.request
        import urllib.error
        try:
            url = f"{self.ollama_config.host}:{self.ollama_config.port}/api/tags"
            urllib.request.urlopen(url, timeout=5)
            return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            return False

    def get_models(self) -> list[str]:
        import urllib.request
        import urllib.error
        try:
            url = f"{self.ollama_config.host}:{self.ollama_config.port}/api/tags"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
                return [m["name"] for m in data.get("models", [])]
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
            return []

    def translate_batch(
        self,
        items: dict[str, str],
        prompt: str,
        config: ProjectConfig,
        on_progress: Optional[Callable] = None,
    ) -> TranslationResult:
        import urllib.request
        import urllib.error

        payload = json.dumps({
            "model": config.model,
            "messages": [
                {"role": "user", "content": f"{prompt}\n{json.dumps(items, indent=4)}"},
            ],
            "stream": False,
        }).encode("utf-8")

        max_retries = 3
        last_error: Optional[str] = None

        for attempt in range(max_retries):
            try:
                url = f"{self.ollama_config.host}:{self.ollama_config.port}/api/chat"
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.ollama_config.timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))

                text = body.get("message", {}).get("content", "")
                if not text:
                    raise RuntimeError("Empty response from Ollama")

                parsed = _parse_json_response(text)
                failed = [k for k in items if k not in parsed]
                return TranslationResult(
                    success=True,
                    data=parsed,
                    failed_keys=failed,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning("Ollama attempt %d failed: %s", attempt + 1, last_error)
                time.sleep(3)

        return TranslationResult(
            success=False,
            data={},
            failed_keys=list(items.keys()),
            error=f"All Ollama attempts failed: {last_error}",
        )


def create_provider(app_config: AppConfig, project_config: ProjectConfig) -> TranslationProvider:
    if project_config.provider == ProviderType.GEMINI:
        return GeminiProvider(api_keys=app_config.get_active_keys("gemini"))
    elif project_config.provider == ProviderType.OLLAMA:
        return OllamaProvider(ollama_config=app_config.ollama)
    else:
        raise ValueError(f"Unknown provider: {project_config.provider}")
