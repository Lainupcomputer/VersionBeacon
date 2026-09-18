"""Small callback-based event system used by the checker."""

from __future__ import annotations

import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, DefaultDict, List, Optional, Union


logger = logging.getLogger(__name__)


class EventName(str, Enum):
    """Events emitted by :class:`VersionChecker`."""

    CHECK_STARTED = "check_started"
    UPDATE_AVAILABLE = "update_available"
    UP_TO_DATE = "up_to_date"
    CURRENT_AHEAD = "current_ahead"
    CHECK_FAILED = "check_failed"
    CHECK_FINISHED = "check_finished"


Callback = Callable[[Any], None]
EventKey = Union[EventName, str]


class EventEmitter:
    """Register and emit simple named callbacks."""

    def __init__(self) -> None:
        self._handlers: DefaultDict[str, List[Callback]] = defaultdict(list)

    @staticmethod
    def _normalize(event: EventKey) -> str:
        return event.value if isinstance(event, EventName) else str(event)

    def on(
        self,
        event: EventKey,
        callback: Optional[Callback] = None,
    ) -> Union[Callback, Callable[[Callback], Callback]]:
        """Register a callback or use ``on`` as a decorator.

        Event callbacks receive the payload for the emitted event. Exceptions
        inside callbacks are logged and do not interrupt the version check.
        """

        event_name = self._normalize(event)

        def register(handler: Callback) -> Callback:
            self._handlers[event_name].append(handler)
            return handler

        if callback is None:
            return register
        return register(callback)

    def off(self, event: EventKey, callback: Callback) -> None:
        """Remove a previously registered callback."""

        handlers = self._handlers.get(self._normalize(event), [])
        if callback in handlers:
            handlers.remove(callback)

    def emit(self, event: EventKey, payload: Any) -> None:
        """Call all handlers for an event."""

        event_name = self._normalize(event)
        for callback in tuple(self._handlers.get(event_name, ())):
            try:
                callback(payload)
            except Exception:
                logger.exception("LUCS-UVC event handler failed: %s", event_name)
