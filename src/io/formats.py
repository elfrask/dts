from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ProviderType(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"


@dataclass
class StringsFile:
    Strings: list[str]


@dataclass
class TranslationDict:
    data: dict[str, str] = field(default_factory=dict)


@dataclass
class UmtConfig:
    cli_path: str = ""
    auto_download: bool = False


@dataclass
class OllamaConfig:
    host: str = "http://localhost:11434"
    timeout: int = 120


@dataclass
class AppConfig:
    """Global application settings (stored in OS user config dir).
    Contains provider credentials and connection config, never project data.
    """
    api_keys: list[str] = field(default_factory=list)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)

    def to_dict(self) -> dict:
        return {
            "api_keys": self.api_keys,
            "ollama_host": self.ollama.host,
            "ollama_timeout": self.ollama.timeout,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        return cls(
            api_keys=data.get("api_keys", []),
            ollama=OllamaConfig(
                host=data.get("ollama_host", "http://localhost:11434"),
                timeout=data.get("ollama_timeout", 120),
            ),
        )


@dataclass
class ProjectConfig:
    route_strings_file: str = ""
    route_input_file: str = "lang_input.json"
    route_output_file: str = "lang_es_out.json"
    route_normalize_file: str = "lang_es_normalize.json"
    route_strings_result_file: str = "strings_es.json"
    route_manual_file: str = "lang_manual_edit.json"

    chunk_size: int = 200
    provider: ProviderType = ProviderType.GEMINI
    prompt: str = ""
    model: str = "gemini-2.5-flash"

    umt: UmtConfig = field(default_factory=UmtConfig)

    def to_dict(self) -> dict:
        return {
            "route_strings_file": self.route_strings_file,
            "route_input_file": self.route_input_file,
            "route_output_file": self.route_output_file,
            "route_strings_result_file": self.route_strings_result_file,
            "route_normalize_file": self.route_normalize_file,
            "route_manual_file": self.route_manual_file,
            "chunk_size": self.chunk_size,
            "provider": self.provider.value,
            "prompt": self.prompt,
            "model": self.model,
            "umt_cli_path": self.umt.cli_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        return cls(
            route_strings_file=data.get("route_strings_file", ""),
            route_input_file=data.get("route_input_file", "lang_input.json"),
            route_output_file=data.get("route_output_file", "lang_es_out.json"),
            route_strings_result_file=data.get("route_strings_result_file", "strings_es.json"),
            route_normalize_file=data.get("route_normalize_file", "lang_es_normalize.json"),
            route_manual_file=data.get("route_manual_file", "lang_manual_edit.json"),
            chunk_size=data.get("chunk_size", 200),
            provider=ProviderType(data.get("provider", "gemini")),
            prompt=data.get("prompt", ""),
            model=data.get("model", "gemini-2.5-flash"),
            umt=UmtConfig(cli_path=data.get("umt_cli_path", "")),
        )


@dataclass
class Project:
    directory: Path
    config: ProjectConfig = field(default_factory=ProjectConfig)

    def resolve_path(self, name: str) -> Path:
        p = Path(name)
        return p if p.is_absolute() else self.directory / p

    @property
    def settings_file(self) -> Path:
        return self.directory / "settings.json"

    @property
    def strings_file_path(self) -> Path:
        return self.resolve_path(self.config.route_strings_file)

    @property
    def input_file_path(self) -> Path:
        return self.resolve_path(self.config.route_input_file)

    @property
    def output_file_path(self) -> Path:
        return self.resolve_path(self.config.route_output_file)

    @property
    def result_file_path(self) -> Path:
        return self.resolve_path(self.config.route_strings_result_file)

    @property
    def normalize_file_path(self) -> Path:
        return self.resolve_path(self.config.route_normalize_file)

    @property
    def manual_file_path(self) -> Path:
        return self.resolve_path(self.config.route_manual_file)


@dataclass
class TranslationResult:
    success: bool
    data: dict[str, str]
    failed_keys: list[str]
    error: Optional[str] = None


@dataclass
class TranslationProgress:
    total: int = 0
    completed: int = 0
    failed: int = 0
    current_key: str = ""
    current_chunk: int = 0
    total_chunks: int = 0
