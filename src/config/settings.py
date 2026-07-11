import json
import logging
from pathlib import Path
from typing import Optional

from src.config.defaults import (
    DEFAULT_SETTINGS_FILE,
    DEFAULT_APP_CONFIG_FILE,
    DEFAULT_PROMPT,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_PORT,
    DEFAULT_OLLAMA_TIMEOUT,
)
from src.io.formats import ProjectConfig, AppConfig, OllamaConfig, Project

logger = logging.getLogger(__name__)


def load_app_settings(path: Optional[Path] = None) -> AppConfig:
    path = path or DEFAULT_APP_CONFIG_FILE

    if not path.exists():
        logger.info(f"App config '{path}' not found. Using defaults.")
        return AppConfig(
            ollama=OllamaConfig(
                host=DEFAULT_OLLAMA_HOST,
                port=DEFAULT_OLLAMA_PORT,
                timeout=DEFAULT_OLLAMA_TIMEOUT,
            ),
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppConfig.from_dict(data)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error reading app config '{path}': {e}. Using defaults.")
        return AppConfig(
            ollama=OllamaConfig(
                host=DEFAULT_OLLAMA_HOST,
                port=DEFAULT_OLLAMA_PORT,
                timeout=DEFAULT_OLLAMA_TIMEOUT,
            ),
        )


def save_app_settings(config: AppConfig, path: Optional[Path] = None) -> None:
    path = path or DEFAULT_APP_CONFIG_FILE

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=4, ensure_ascii=False)
        logger.info(f"App config saved to '{path}'")
    except IOError as e:
        logger.error(f"Error saving app config to '{path}': {e}")
        raise


def load_settings(settings_path: Optional[str] = None) -> ProjectConfig:
    path = Path(settings_path) if settings_path else Path(DEFAULT_SETTINGS_FILE)

    if not path.exists():
        logger.info(f"Config file '{path}' not found. Using defaults.")
        return ProjectConfig(
            prompt=DEFAULT_PROMPT,
            chunk_size=DEFAULT_CHUNK_SIZE,
            model=DEFAULT_MODEL,
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectConfig.from_dict(data)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error reading '{path}': {e}. Using defaults.")
        return ProjectConfig(
            prompt=DEFAULT_PROMPT,
            chunk_size=DEFAULT_CHUNK_SIZE,
            model=DEFAULT_MODEL,
        )


def save_settings(config: ProjectConfig, settings_path: Optional[str] = None) -> None:
    path = Path(settings_path) if settings_path else Path(DEFAULT_SETTINGS_FILE)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=4, ensure_ascii=False)
        logger.info(f"Config saved to '{path}'")
    except IOError as e:
        logger.error(f"Error saving config to '{path}': {e}")
        raise


def load_project(project_dir: Path) -> Project:
    settings_file = project_dir / DEFAULT_SETTINGS_FILE
    config = load_settings(str(settings_file))
    return Project(directory=project_dir, config=config)


def save_project(project: Project) -> None:
    save_settings(project.config, str(project.settings_file))
