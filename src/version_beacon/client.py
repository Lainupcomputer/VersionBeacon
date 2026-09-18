"""The public version-checking client."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Mapping, Optional, Union
from urllib import error as urllib_error
from urllib import request as urllib_request

from .config import DEFAULT_ENV_PREFIX, VersionBeaconConfig
from .events import EventEmitter, EventKey, EventName
from .exceptions import (
    VersionBeaconError,
    VersionFetchError,
    VersionResponseError,
)
from .models import CheckResult, CheckStarted, CheckStatus
from .versions import parse_version


logger = logging.getLogger(__name__)
_VERSION_TEXT = r"\d+\.\d+\.\d+(?:\.\d+)?"


@dataclass(frozen=True)
class VersionMetadata:
    """Normalized data returned by a version endpoint."""

    version: str
    release_url: Optional[str] = None
    release_notes: Optional[str] = None


def _parse_response(payload: bytes, app_name: str) -> VersionMetadata:
    try:
        text = payload.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise VersionResponseError("Version response is not valid UTF-8.") from exc

    if not text:
        raise VersionResponseError("Version response is empty.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Keep the original endpoint format usable while migrating to JSON.
        pattern = re.compile(
            rf"{re.escape(app_name)}_version\s*==\s*({_VERSION_TEXT})"
        )
        match = pattern.search(text)
        if match is None:
            raise VersionResponseError(
                "Response is neither valid JSON nor a supported text response."
            )
        return VersionMetadata(version=match.group(1))

    if not isinstance(data, dict):
        raise VersionResponseError("JSON response must be an object.")

    response_app = data.get("app_name", data.get("application"))
    if response_app is not None and response_app != app_name:
        raise VersionResponseError(
            f"Response belongs to '{response_app}', not '{app_name}'."
        )

    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        raise VersionResponseError("JSON response must contain a string 'version'.")

    release_url = data.get("release_url", data.get("url"))
    if release_url is not None and not isinstance(release_url, str):
        raise VersionResponseError("'release_url' must be a string when provided.")

    release_notes = data.get("release_notes", data.get("notes"))
    if release_notes is not None and not isinstance(release_notes, str):
        raise VersionResponseError("'release_notes' must be a string when provided.")

    return VersionMetadata(
        version=version.strip(),
        release_url=release_url,
        release_notes=release_notes,
    )


class VersionChecker:
    """Check an application's installed version against a remote version."""

    def __init__(
        self,
        config: Optional[VersionBeaconConfig] = None,
        *,
        app_name: Optional[str] = None,
        current_version: Optional[str] = None,
        version_url: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        max_response_bytes: Optional[int] = None,
        user_agent: Optional[str] = None,
        env_prefix: str = DEFAULT_ENV_PREFIX,
        events: Optional[EventEmitter] = None,
    ) -> None:
        if config is not None and any(
            value is not None
            for value in (
                app_name,
                current_version,
                version_url,
                timeout,
                retries,
                max_response_bytes,
                user_agent,
            )
        ):
            raise ValueError("Pass either config or individual configuration values, not both.")

        self.config = config or VersionBeaconConfig.from_sources(
            app_name=app_name,
            current_version=current_version,
            version_url=version_url,
            timeout=timeout,
            retries=retries,
            max_response_bytes=max_response_bytes,
            user_agent=user_agent,
            prefix=env_prefix,
        )
        self.events = events or EventEmitter()

    @classmethod
    def from_env(
        cls,
        prefix: str = DEFAULT_ENV_PREFIX,
        *,
        events: Optional[EventEmitter] = None,
    ) -> "VersionChecker":
        """Create a checker from ``VERSION_BEACON_*`` environment variables."""

        return cls(config=VersionBeaconConfig.from_env(prefix), events=events)

    def on(
        self,
        event: EventKey,
        callback: Optional[Callable[[Any], None]] = None,
    ) -> Any:
        """Register a callback or use the method as a decorator."""

        return self.events.on(event, callback)

    def off(self, event: EventKey, callback: Callable[[Any], None]) -> None:
        """Remove a previously registered event callback."""

        self.events.off(event, callback)

    def check(self) -> CheckResult:
        """Perform one check and return a structured result.

        Network and response failures are represented by a failed result so a
        version check can safely run during application startup. Configuration
        errors are detected while creating the checker.
        """

        started_at = datetime.now(timezone.utc)
        self.events.emit(
            EventName.CHECK_STARTED,
            CheckStarted(
                app_name=self.config.app_name,
                current_version=self.config.current_version,
                started_at=started_at,
            ),
        )

        try:
            current = parse_version(self.config.current_version)
            payload = self._fetch()
            metadata = _parse_response(payload, self.config.app_name)
            latest = parse_version(metadata.version)

            if latest > current:
                status = CheckStatus.UPDATE_AVAILABLE
            elif latest < current:
                status = CheckStatus.CURRENT_AHEAD
            else:
                status = CheckStatus.UP_TO_DATE

            result = CheckResult(
                app_name=self.config.app_name,
                current_version=current.original,
                latest_version=latest.original,
                status=status,
                checked_at=datetime.now(timezone.utc),
                version_url=self.config.version_url,
                release_url=metadata.release_url,
                release_notes=metadata.release_notes,
            )
        except Exception as exc:
            if not isinstance(exc, VersionBeaconError):
                logger.debug("Unexpected VersionBeacon check error", exc_info=True)
            result = CheckResult(
                app_name=self.config.app_name,
                current_version=self.config.current_version,
                latest_version=None,
                status=CheckStatus.FAILED,
                checked_at=datetime.now(timezone.utc),
                version_url=self.config.version_url,
                error=str(exc),
            )

        if result.status is CheckStatus.UPDATE_AVAILABLE:
            event = EventName.UPDATE_AVAILABLE
        elif result.status is CheckStatus.UP_TO_DATE:
            event = EventName.UP_TO_DATE
        elif result.status is CheckStatus.CURRENT_AHEAD:
            event = EventName.CURRENT_AHEAD
        else:
            event = EventName.CHECK_FAILED

        self.events.emit(event, result)
        self.events.emit(EventName.CHECK_FINISHED, result)
        return result

    def _fetch(self) -> bytes:
        request = urllib_request.Request(
            self.config.version_url,
            headers={
                "Accept": "application/json, text/plain;q=0.9, */*;q=0.1",
                "User-Agent": self.config.user_agent,
            },
            method="GET",
        )

        attempts = self.config.retries + 1
        for attempt in range(attempts):
            try:
                with urllib_request.urlopen(
                    request,
                    timeout=self.config.timeout,
                ) as response:
                    payload = response.read(self.config.max_response_bytes + 1)
                if len(payload) > self.config.max_response_bytes:
                    raise VersionFetchError(
                        "Version response exceeds the configured size limit."
                    )
                return payload
            except VersionFetchError:
                raise
            except (urllib_error.URLError, TimeoutError, OSError) as exc:
                if attempt + 1 >= attempts:
                    raise VersionFetchError(
                        f"Could not fetch version information: {exc}"
                    ) from exc
                time.sleep(min(0.25 * (attempt + 1), 1.0))

        raise VersionFetchError("Could not fetch version information.")
