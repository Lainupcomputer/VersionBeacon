"""VersionBeacon: a simple application version checker."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from .client import VersionChecker
from .config import VersionBeaconConfig
from .events import EventEmitter, EventName
from .exceptions import (
    ConfigurationError,
    InvalidVersionError,
    VersionBeaconError,
    VersionFetchError,
    VersionResponseError,
)
from .models import CheckResult, CheckStarted, CheckStatus
from .versions import Version, parse_version

__all__ = [
    "VersionChecker",
    "VersionBeaconConfig",
    "EventEmitter",
    "EventName",
    "CheckResult",
    "CheckStarted",
    "CheckStatus",
    "Version",
    "parse_version",
    "check",
    "VersionBeaconError",
    "ConfigurationError",
    "InvalidVersionError",
    "VersionFetchError",
    "VersionResponseError",
]

__version__ = "2.0.0"


def check(
    *,
    config: Optional[VersionBeaconConfig] = None,
    app_name: Optional[str] = None,
    current_version: Optional[str] = None,
    version_url: Optional[str] = None,
    timeout: Optional[float] = None,
    retries: Optional[int] = None,
    max_response_bytes: Optional[int] = None,
    user_agent: Optional[str] = None,
    env_prefix: str = "VERSION_BEACON_",
    events: Optional[Mapping[str, Callable[[Any], None]]] = None,
    on_update_available: Optional[Callable[[CheckResult], None]] = None,
    on_up_to_date: Optional[Callable[[CheckResult], None]] = None,
    on_current_ahead: Optional[Callable[[CheckResult], None]] = None,
    on_check_failed: Optional[Callable[[CheckResult], None]] = None,
    on_finished: Optional[Callable[[CheckResult], None]] = None,
) -> CheckResult:
    """One-call wrapper around :class:`VersionChecker`.

    When configuration arguments are omitted, values are read from
    ``VERSION_BEACON_APP_NAME``, ``VERSION_BEACON_CURRENT_VERSION`` and
    ``VERSION_BEACON_VERSION_URL``.
    """

    checker = VersionChecker(
        config=config,
        app_name=app_name,
        current_version=current_version,
        version_url=version_url,
        timeout=timeout,
        retries=retries,
        max_response_bytes=max_response_bytes,
        user_agent=user_agent,
        env_prefix=env_prefix,
    )

    for event, callback in (events or {}).items():
        checker.on(event, callback)

    callbacks = {
        EventName.UPDATE_AVAILABLE: on_update_available,
        EventName.UP_TO_DATE: on_up_to_date,
        EventName.CURRENT_AHEAD: on_current_ahead,
        EventName.CHECK_FAILED: on_check_failed,
        EventName.CHECK_FINISHED: on_finished,
    }
    for event, callback in callbacks.items():
        if callback is not None:
            checker.on(event, callback)

    return checker.check()
