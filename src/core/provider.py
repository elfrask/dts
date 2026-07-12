import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable

import google.genai as genai
from google.genai import types
import ollama

from src.io.formats import (
    ProjectConfig,
    AppConfig,
    TranslationResult,
    ProviderType,
    OllamaConfig,
)
from src.config.defaults import OPENAI_COMPATIBLE_BASE_URLS
from src.core.api_manager import ApiKeyManager

logger = logging.getLogger(__name__)

# Shared config that disables thinking for all Gemini models
_NO_THINKING_CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(include_thoughts=False),
)


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
                payload = f"{prompt}\n{json.dumps(items, indent=4)}"
                response = client.models.generate_content(
                    model=config.model,
                    contents=payload,
                    config=_NO_THINKING_CONFIG,
                )

                if not response.candidates or not response.candidates[0].content.parts: #type: ignore
                    raise RuntimeError("Empty response from Gemini")

                text: str = response.candidates[0].content.parts[0].text #type: ignore
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
        self._client = ollama.Client(host=f"{ollama_config.host}:{ollama_config.port}")

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def get_models(self) -> list[str]:
        try:
            resp = self._client.list()
            return [m.model for m in resp.models]  # type: ignore
        except Exception:
            return []

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
            try:
                resp = self._client.chat(
                    model=config.model,
                    messages=[
                        {
                            "role": "user",
                            # "content": f"{prompt}\n{json.dumps(items, indent=4)}",
                            "content": f"Responde EXCLUSIVAMENTE con el objeto JSON solicitado sin notas ni análisis previos.\n{prompt}\n{json.dumps(items, indent=4)}",
                        },
                    ],
                    stream=False,
                    think=False,
                    format="json"
                )
                text = resp.message.content or ""
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


class OpenAICompatibleProvider(TranslationProvider):
    """For providers with OpenAI-compatible API: Groq, DeepInfra, Together, OpenAI."""

    def __init__(self, api_keys: list[str], provider_name: str, base_url: str):
        self._key_manager = ApiKeyManager(api_keys)
        self._provider_name = provider_name
        self._base_url = base_url

    @property
    def name(self) -> str:
        return self._provider_name

    def is_available(self) -> bool:
        return self._key_manager.key_count > 0

    def get_models(self) -> list[str]:
        from src.config.defaults import PROVIDER_MODELS
        return PROVIDER_MODELS.get(self._provider_name, [])

    def translate_batch(
        self,
        items: dict[str, str],
        prompt: str,
        config: ProjectConfig,
        on_progress: Optional[Callable] = None,
    ) -> TranslationResult:
        from openai import OpenAI, APIError

        max_retries = 3
        last_error: Optional[str] = None

        for attempt in range(max_retries):
            key = self._key_manager.next_key()
            logger.info(
                "OpenAI-compatible %s attempt %d/%d",
                self._provider_name, attempt + 1, max_retries,
            )

            try:
                client = OpenAI(api_key=key, base_url=self._base_url)
                payload = f"{prompt}\n{json.dumps(items, indent=4)}"
                response = client.chat.completions.create(
                    model=config.model,
                    messages=[
                        {"role": "user", "content": payload},
                    ],
                    response_format={"type": "json_object"},
                )
                text = response.choices[0].message.content or ""
                if not text:
                    raise RuntimeError("Empty response from provider")

                parsed = _parse_json_response(text)
                failed = [k for k in items if k not in parsed]
                return TranslationResult(
                    success=True,
                    data=parsed,
                    failed_keys=failed,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "%s attempt %d failed: %s",
                    self._provider_name, attempt + 1, last_error,
                )
                self._key_manager.rotate()
                time.sleep(3)

        return TranslationResult(
            success=False,
            data={},
            failed_keys=list(items.keys()),
            error=f"All {self._provider_name} attempts failed: {last_error}",
        )


class AnthropicProvider(TranslationProvider):
    def __init__(self, api_keys: list[str]):
        self._key_manager = ApiKeyManager(api_keys)

    @property
    def name(self) -> str:
        return "anthropic"

    def is_available(self) -> bool:
        return self._key_manager.key_count > 0

    def get_models(self) -> list[str]:
        from src.config.defaults import ANTHROPIC_MODELS
        return ANTHROPIC_MODELS[:]

    def translate_batch(
        self,
        items: dict[str, str],
        prompt: str,
        config: ProjectConfig,
        on_progress: Optional[Callable] = None,
    ) -> TranslationResult:
        import anthropic 

        max_retries = 3
        last_error: Optional[str] = None

        for attempt in range(max_retries):
            key = self._key_manager.next_key()
            logger.info("Anthropic attempt %d/%d", attempt + 1, max_retries)

            try:
                client = anthropic.Anthropic(api_key=key)
                payload = f"{prompt}\n{json.dumps(items, indent=4)}"
                response = client.messages.create(
                    model=config.model,
                    max_tokens=8192,
                    messages=[
                        {"role": "user", "content": payload},
                    ],
                )
                text: str = response.content[0].text if response.content else "" #type: ignore
                if not text:
                    raise RuntimeError("Empty response from Anthropic")

                parsed = _parse_json_response(text)
                failed = [k for k in items if k not in parsed]
                return TranslationResult(
                    success=True,
                    data=parsed,
                    failed_keys=failed,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning("Anthropic attempt %d failed: %s", attempt + 1, last_error)
                self._key_manager.rotate()
                time.sleep(3)

        return TranslationResult(
            success=False,
            data={},
            failed_keys=list(items.keys()),
            error=f"All Anthropic attempts failed: {last_error}",
        )


def create_provider(app_config: AppConfig, project_config: ProjectConfig) -> TranslationProvider:
    provider_name = project_config.provider.value

    if project_config.provider == ProviderType.GEMINI:
        return GeminiProvider(api_keys=app_config.get_active_keys("gemini"))

    elif project_config.provider == ProviderType.OLLAMA:
        return OllamaProvider(ollama_config=app_config.ollama)

    elif project_config.provider == ProviderType.ANTHROPIC:
        return AnthropicProvider(api_keys=app_config.get_active_keys("anthropic"))

    elif project_config.provider == ProviderType.OPENAI:
        return OpenAICompatibleProvider(
            api_keys=app_config.get_active_keys("openai"),
            provider_name="openai",
            base_url="https://api.openai.com/v1",
        )

    elif provider_name in OPENAI_COMPATIBLE_BASE_URLS:
        return OpenAICompatibleProvider(
            api_keys=app_config.get_active_keys(provider_name),
            provider_name=provider_name,
            base_url=OPENAI_COMPATIBLE_BASE_URLS[provider_name],
        )

    else:
        raise ValueError(f"Unknown provider: {project_config.provider}")
