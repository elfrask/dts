from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.io.formats import AppConfig, Project


@dataclass
class LogEntry:
    level: str
    message: str


class GUIState:
    def __init__(self, app_config: AppConfig) -> None:
        self.app_config = app_config
        self.project: Optional[Project] = None
        self.log_entries: list[LogEntry] = field(default_factory=list)

    def add_log(self, level: str, message: str) -> None:
        self.log_entries.append(LogEntry(level=level, message=message))

    def clear_log(self) -> None:
        self.log_entries.clear()
