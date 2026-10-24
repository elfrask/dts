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
from src.config.defaults import (
    OPENAI_COMPATIBLE_BASE_URLS,
    DEFAULT_OLLAMA_SINGLE_PROMPT,
    COMMANDCODE_BASE_URL,
    COMMANDCODE_ANTHROPIC_BASE_URL,
)
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

    def translate_single(
        self,
        key: str,
        text: str,
        prompt: str,
        config: ProjectConfig,
    ) -> str:
        raise NotImplementedError(
            f"Single-dialog translation is not supported by {self.name}"
        )

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
        from src.config.defaults import GEMINI_MODELS
        from src.core.model_catalog import fetch_gemini_models

        if self._key_manager.key_count:
            live = fetch_gemini_models(self._key_manager.current_key)
            if live:
                return live
        return GEMINI_MODELS[:]

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

                meta = getattr(response, "usage_metadata", None)
                in_tok = int(getattr(meta, "prompt_token_count", 0) or 0) if meta else 0
                out_tok = int(getattr(meta, "candidates_token_count", 0) or 0) if meta else 0
                return TranslationResult(
                    success=True,
                    data=parsed,
                    failed_keys=failed,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    attempts=attempt + 1,
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
                in_tok = int(getattr(resp, "prompt_eval_count", 0) or 0)
                out_tok = int(getattr(resp, "eval_count", 0) or 0)
                return TranslationResult(
                    success=True,
                    data=parsed,
                    failed_keys=failed,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    attempts=attempt + 1,
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

    def translate_single(
        self,
        key: str,
        text: str,
        prompt: str,
        config: ProjectConfig,
    ) -> str:
        effective_prompt = prompt or DEFAULT_OLLAMA_SINGLE_PROMPT
        payload = f"{effective_prompt}\n\nDialogo:\n{text}"

        resp = self._client.chat(
            model=config.model,
            messages=[{"role": "user", "content": payload}],
            stream=False,
        )
        result = (resp.message.content or "").strip()
        if not result:
            raise RuntimeError(f"Empty response from Ollama for key '{key}'")
        return result


class OpenAICompatibleProvider(TranslationProvider):
    """For providers with OpenAI-compatible API: Groq, DeepInfra, Together, OpenAI."""

    def __init__(
        self,
        api_keys: list[str],
        provider_name: str,
        base_url: str,
        known_models: Optional[list[str]] = None,
    ):
        self._key_manager = ApiKeyManager(api_keys)
        self._provider_name = provider_name
        self._base_url = base_url
        self._known_models = list(known_models or [])

    @property
    def name(self) -> str:
        return self._provider_name

    def is_available(self) -> bool:
        return self._key_manager.key_count > 0

    def get_models(self) -> list[str]:
        """Ask the endpoint for its model list, falling back to known ones."""
        from src.config.defaults import PROVIDER_MODELS
        from src.core.model_catalog import fetch_openai_models

        if self._key_manager.key_count:
            live = fetch_openai_models(self._base_url, self._key_manager.current_key)
            if live:
                return live
        return self._known_models or PROVIDER_MODELS.get(self._provider_name, [])

    def translate_batch(
        self,
        items: dict[str, str],
        prompt: str,
        config: ProjectConfig,
        on_progress: Optional[Callable] = None,
    ) -> TranslationResult:
        from src.core.http_client import post_json, join_url

        max_retries = 3
        last_error: Optional[str] = None
        url = join_url(self._base_url, "chat/completions")

        for attempt in range(max_retries):
            key = self._key_manager.next_key()
            logger.info(
                "OpenAI-compatible %s attempt %d/%d",
                self._provider_name, attempt + 1, max_retries,
            )

            try:
                content = f"{prompt}\n{json.dumps(items, indent=4)}"
                # First attempt asks for strict JSON; retries drop the param for
                # endpoints that do not implement ``response_format``.
                body: dict = {
                    "model": config.model,
                    "messages": [{"role": "user", "content": content}],
                }
                if attempt == 0:
                    body["response_format"] = {"type": "json_object"}

                response = post_json(url, body, key)
                choices = response.get("choices") or []
                text = ""
                if choices:
                    text = (choices[0].get("message") or {}).get("content") or ""
                if not text:
                    raise RuntimeError("Empty response from provider")

                parsed = _parse_json_response(text)
                failed = [k for k in items if k not in parsed]
                usage = response.get("usage") or {}
                in_tok = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
                out_tok = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
                return TranslationResult(
                    success=True,
                    data=parsed,
                    failed_keys=failed,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    attempts=attempt + 1,
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


class CommandCodeProvider(OpenAICompatibleProvider):
    """CommandCode provider (https://commandcode.ai/docs/provider).

    Most models use the OpenAI Chat Completions endpoint, but Claude models are
    only served on the Anthropic Messages endpoint, so requests are routed based
    on the selected model id.
    """

    def __init__(self, api_keys: list[str], known_models: Optional[list[str]] = None):
        super().__init__(
            api_keys=api_keys,
            provider_name="commandcode",
            base_url=COMMANDCODE_BASE_URL,
            known_models=known_models,
        )
        self._anthropic = AnthropicProvider(
            api_keys=api_keys,
            base_url=COMMANDCODE_ANTHROPIC_BASE_URL,
            provider_name="commandcode",
        )

    @staticmethod
    def _is_claude(model: str) -> bool:
        return "claude" in str(model).lower()

    def get_models(self) -> list[str]:
        from src.config.defaults import COMMANDCODE_MODELS
        from src.core.model_catalog import fetch_commandcode_models

        if self._key_manager.key_count:
            live = fetch_commandcode_models(self._key_manager.current_key)
            if live:
                return live
        return self._known_models or COMMANDCODE_MODELS[:]

    def translate_batch(
        self,
        items: dict[str, str],
        prompt: str,
        config: ProjectConfig,
        on_progress: Optional[Callable] = None,
    ) -> TranslationResult:
        if self._is_claude(config.model):
            return self._anthropic.translate_batch(items, prompt, config, on_progress)
        return super().translate_batch(items, prompt, config, on_progress)


class AnthropicProvider(TranslationProvider):
    def __init__(
        self,
        api_keys: list[str],
        base_url: Optional[str] = None,
        provider_name: str = "anthropic",
        known_models: Optional[list[str]] = None,
    ):
        self._key_manager = ApiKeyManager(api_keys)
        self._base_url = base_url or None
        self._provider_name = provider_name
        self._known_models = list(known_models or [])

    @property
    def name(self) -> str:
        return self._provider_name

    def is_available(self) -> bool:
        return self._key_manager.key_count > 0

    def get_models(self) -> list[str]:
        from src.config.defaults import ANTHROPIC_MODELS
        from src.core.model_catalog import fetch_anthropic_models

        if self._key_manager.key_count:
            live = fetch_anthropic_models(
                self._key_manager.current_key, self._base_url,
            )
            if live:
                return live
        return self._known_models or ANTHROPIC_MODELS[:]

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
                client = (
                    anthropic.Anthropic(api_key=key, base_url=self._base_url)
                    if self._base_url
                    else anthropic.Anthropic(api_key=key)
                )
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
                usage = getattr(response, "usage", None)
                in_tok = int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
                out_tok = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
                return TranslationResult(
                    success=True,
                    data=parsed,
                    failed_keys=failed,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    attempts=attempt + 1,
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
    provider_name = str(getattr(project_config.provider, "value", project_config.provider))

    # ── User-defined providers take priority over built-ins ────
    custom = app_config.get_custom_provider(provider_name)
    if custom is not None:
        keys = app_config.get_active_keys(custom.name)
        if custom.api_type != "anthropic" and not custom.base_url:
            raise ValueError(
                f"El proveedor personalizado '{custom.name}' necesita una Base URL "
                "(por ejemplo http://localhost:8000/v1)."
            )
        if custom.api_type == "anthropic":
            return AnthropicProvider(
                api_keys=keys,
                base_url=custom.base_url or None,
                provider_name=custom.name,
                known_models=custom.models,
            )
        return OpenAICompatibleProvider(
            api_keys=keys,
            provider_name=custom.name,
            base_url=custom.base_url,
            known_models=custom.models,
        )

    if provider_name == ProviderType.GEMINI.value:
        return GeminiProvider(api_keys=app_config.get_active_keys("gemini"))

    elif provider_name == ProviderType.COMMANDCODE.value:
        return CommandCodeProvider(api_keys=app_config.get_active_keys("commandcode"))

    elif provider_name == ProviderType.OLLAMA.value:
        return OllamaProvider(ollama_config=app_config.ollama)

    elif provider_name == ProviderType.ANTHROPIC.value:
        return AnthropicProvider(api_keys=app_config.get_active_keys("anthropic"))

    elif provider_name == ProviderType.OPENAI.value:
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
        raise ValueError(f"Unknown provider: {provider_name}")
