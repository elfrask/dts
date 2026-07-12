from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ProviderType(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"
    GROQ = "groq"
    DEEPINFRA = "deepinfra"
    TOGETHER = "together"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass
class StringsFile:
    Strings: list[str]


@dataclass
class TranslationDict:
    data: dict[str, str] = field(default_factory=dict)


@dataclass
class ApiKeyEntry:
    name: str = ""
    key: str = ""
    enabled: bool = True


@dataclass
class ProviderKeys:
    """API keys per provider, not global."""
    keys: list[ApiKeyEntry] = field(default_factory=list)


@dataclass
class OllamaConfig:
    host: str = "http://localhost"
    port: int = 11434
    timeout: int = 120


@dataclass
class UmtConfig:
    directory: str = ""
    auto_download: bool = False


@dataclass
class AppConfig:
    """Global application settings (stored in OS user config dir).
    Contains provider credentials and connection config, never project data.
    """
    providers: dict[str, ProviderKeys] = field(default_factory=dict)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    umt: UmtConfig = field(default_factory=UmtConfig)

    def get_active_keys(self, provider: str) -> list[str]:
        """Return enabled key strings for a provider."""
        p = self.providers.get(provider)
        if not p:
            return []
        return [k.key for k in p.keys if k.enabled and k.key]

    def to_dict(self) -> dict:
        return {
            "providers": {
                name: {
                    "keys": [
                        {"name": k.name, "key": k.key, "enabled": k.enabled}
                        for k in p.keys
                    ]
                }
                for name, p in self.providers.items()
            },
            "ollama_host": self.ollama.host,
            "ollama_port": self.ollama.port,
            "ollama_timeout": self.ollama.timeout,
            "umt_directory": self.umt.directory,
            "umt_auto_download": self.umt.auto_download,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        providers: dict[str, ProviderKeys] = {}
        for name, pdata in data.get("providers", {}).items():
            keys = [
                ApiKeyEntry(
                    name=k.get("name", ""),
                    key=k.get("key", ""),
                    enabled=k.get("enabled", True),
                )
                for k in pdata.get("keys", [])
            ]
            providers[name] = ProviderKeys(keys=keys)

        # Backward compat: migrate flat api_keys to gemini provider
        old_keys = data.get("api_keys")
        if old_keys and "gemini" not in providers:
            providers["gemini"] = ProviderKeys(
                keys=[ApiKeyEntry(name=f"key{i+1}", key=k, enabled=True) for i, k in enumerate(old_keys)]
            )

        host_raw = data.get("ollama_host", "http://localhost")
        # Strip port from old combined format (e.g. "http://localhost:11434")
        if host_raw.count(":") == 2 and host_raw.rsplit(":", 1)[1].isdigit():
            host_raw = host_raw.rsplit(":", 1)[0]

        # Backward compat: migra "umt_cli_path" (exe) a "umt_directory" (carpeta)
        raw_dir = data.get("umt_directory") or data.get("umt_cli_path", "")
        if raw_dir and Path(raw_dir).is_file():
            raw_dir = str(Path(raw_dir).parent)

        return cls(
            providers=providers,
            ollama=OllamaConfig(
                host=host_raw,
                port=data.get("ollama_port", 11434),
                timeout=data.get("ollama_timeout", 120),
            ),
            umt=UmtConfig(
                directory=raw_dir,
                auto_download=data.get("umt_auto_download", False),
            ),
        )


@dataclass
class ProjectConfig:
    route_strings_file: str = "strings.json"
    route_data_win: str = ""
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
            "route_data_win": self.route_data_win,
            "route_input_file": self.route_input_file,
            "route_output_file": self.route_output_file,
            "route_strings_result_file": self.route_strings_result_file,
            "route_normalize_file": self.route_normalize_file,
            "route_manual_file": self.route_manual_file,
            "chunk_size": self.chunk_size,
            "provider": self.provider.value,
            "prompt": self.prompt,
            "model": self.model,
            "umt_directory": self.umt.directory,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        raw_dir = data.get("umt_directory") or data.get("umt_cli_path", "")
        if raw_dir and Path(raw_dir).is_file():
            raw_dir = str(Path(raw_dir).parent)
        return cls(
            route_strings_file=data.get("route_strings_file", "strings.json"),
            route_data_win=data.get("route_data_win", ""),
            route_input_file=data.get("route_input_file", "lang_input.json"),
            route_output_file=data.get("route_output_file", "lang_es_out.json"),
            route_strings_result_file=data.get("route_strings_result_file", "strings_es.json"),
            route_normalize_file=data.get("route_normalize_file", "lang_es_normalize.json"),
            route_manual_file=data.get("route_manual_file", "lang_manual_edit.json"),
            chunk_size=data.get("chunk_size", 200),
            provider=ProviderType(data.get("provider", "gemini")),
            prompt=data.get("prompt", ""),
            model=data.get("model", "gemini-2.5-flash"),
            umt=UmtConfig(directory=raw_dir),
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
    def data_win_file_path(self) -> Path:
        return self.resolve_path(self.config.route_data_win)

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
