import logging

logger = logging.getLogger(__name__)


class ApiKeyManager:
    def __init__(self, api_keys: list[str]):
        self.api_keys = api_keys
        self._index = 0

    def next_key(self) -> str:
        if not self.api_keys:
            raise ValueError("No API keys configured")
        key = self.api_keys[self._index % len(self.api_keys)]
        self._index += 1
        return key

    def rotate(self) -> None:
        self._index += 1
        logger.info(f"Rotated to API key index {self._index % len(self.api_keys)}")

    @property
    def current_key(self) -> str:
        if not self.api_keys:
            return ""
        return self.api_keys[self._index % len(self.api_keys)]

    @property
    def key_count(self) -> int:
        return len(self.api_keys)
