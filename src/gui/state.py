from pathlib import Path
from typing import Optional

from src.io.formats import AppConfig, Project


class LogEntry:
    def __init__(self, level: str, message: str) -> None:
        self.level = level
        self.message = message


class GUIState:
    def __init__(self, app_config: AppConfig) -> None:
        self.app_config = app_config
        self.project: Optional[Project] = None
        self.log_entries: list[LogEntry] = []

    def add_log(self, level: str, message: str) -> None:
        self.log_entries.append(LogEntry(level=level, message=message))

    def clear_log(self) -> None:
        self.log_entries.clear()
