from abc import ABC, abstractmethod
from typing import Optional, Callable

from src.io.formats import ProjectConfig, AppConfig, TranslationResult, ProviderType, OllamaConfig


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
    def __init__(self, api_keys: list[str]):
        self.api_keys = api_keys

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return len(self.api_keys) > 0

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
    def __init__(self, ollama_config: OllamaConfig):
        self.ollama_config = ollama_config

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        import urllib.request
        import urllib.error
        try:
            url = f"{self.ollama_config.host}/api/tags"
            urllib.request.urlopen(url, timeout=5)
            return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            return False

    def get_models(self) -> list[str]:
        import json
        import urllib.request
        import urllib.error
        try:
            url = f"{self.ollama_config.host}/api/tags"
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


def create_provider(app_config: AppConfig, project_config: ProjectConfig) -> TranslationProvider:
    if project_config.provider == ProviderType.GEMINI:
        return GeminiProvider(api_keys=app_config.api_keys)
    elif project_config.provider == ProviderType.OLLAMA:
        return OllamaProvider(ollama_config=app_config.ollama)
    else:
        raise ValueError(f"Unknown provider: {project_config.provider}")
