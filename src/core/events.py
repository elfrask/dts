import logging
from enum import Enum
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class Signal(Enum):
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETE = "complete"
    LOG = "log"


class EventBus:
    def __init__(self):
        self._listeners: dict[Signal, list[Callable]] = {
            signal: [] for signal in Signal
        }

    def on(self, signal: Signal, callback: Callable) -> None:
        if callback not in self._listeners[signal]:
            self._listeners[signal].append(callback)

    def off(self, signal: Signal, callback: Callable) -> None:
        if callback in self._listeners[signal]:
            self._listeners[signal].remove(callback)

    def emit(self, signal: Signal, **kwargs: Any) -> None:
        for callback in self._listeners[signal]:
            try:
                callback(**kwargs)
            except Exception as e:
                logger.error(f"Error in event handler for {signal.value}: {e}")

    def emit_progress(self, current: int, total: int, message: str = "") -> None:
        self.emit(Signal.PROGRESS, current=current, total=total, message=message)

    def emit_error(self, message: str, exception: Optional[Exception] = None) -> None:
        self.emit(Signal.ERROR, message=message, exception=exception)

    def emit_complete(self, result: Any = None) -> None:
        self.emit(Signal.COMPLETE, result=result)

    def emit_log(self, level: str, message: str) -> None:
        self.emit(Signal.LOG, level=level, message=message)


_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
