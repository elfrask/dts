from abc import ABC, abstractmethod
from typing import Optional, Callable

from src.io.formats import ProjectConfig, TranslationResult, ProviderType


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


class GeminiProvider(TranslationProvider):
    def __init__(self, config: ProjectConfig):
        self.config = config

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return len(self.config.api_keys) > 0

    def get_models(self) -> list[str]:
        return [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]

    def translate_batch(
        self,
        items: dict[str, str],
        prompt: str,
        config: ProjectConfig,
        on_progress: Optional[Callable] = None,
    ) -> TranslationResult:
        raise NotImplementedError("Fase 2: implementar con google-genai SDK")


class OllamaProvider(TranslationProvider):
    def __init__(self, config: ProjectConfig):
        self.config = config

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        import urllib.request
        import urllib.error
        try:
            url = f"{self.config.ollama.host}/api/tags"
            urllib.request.urlopen(url, timeout=5)
            return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            return False

    def get_models(self) -> list[str]:
        import json
        import urllib.request
        import urllib.error
        try:
            url = f"{self.config.ollama.host}/api/tags"
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
        raise NotImplementedError("Fase 2: implementar con Ollama REST API")


def create_provider(config: ProjectConfig) -> TranslationProvider:
    if config.provider == ProviderType.GEMINI:
        return GeminiProvider(config)
    elif config.provider == ProviderType.OLLAMA:
        return OllamaProvider(config)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")
