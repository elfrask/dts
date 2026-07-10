import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PromptManager:
    def __init__(self, template: str = ""):
        self._template = template

    @property
    def template(self) -> str:
        return self._template

    @template.setter
    def template(self, value: str) -> None:
        self._template = value

    def build(self, data: dict[str, str]) -> str:
        return f"{self._template}\n{json.dumps(data, indent=4)}"
