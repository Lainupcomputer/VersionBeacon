"""Configuration handling for VersionBeacon."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Optional
from urllib.parse import urlparse

from .exceptions import ConfigurationError


DEFAULT_ENV_PREFIX = "VERSION_BEACON_"
DEFAULT_TIMEOUT = 5.0
DEFAULT_RETRIES = 0
DEFAULT_MAX_RESPONSE_BYTES = 1024 * 1024
DEFAULT_USER_AGENT = "version-beacon/2"


def _environment_value(
    environment: Mapping[str, str],
    prefix: str,
    name: str,
) -> Optional[str]:
    value = environment.get(f"{prefix}{name}")
    if value is None:
        return None
    value = value.strip()
    return value or None


def _required_value(
    explicit: Optional[str],
    environment: Mapping[str, str],
    prefix: str,
    name: str,
) -> str:
    value = explicit if explicit is not None else _environment_value(environment, prefix, name)
    if value is None or not value.strip():
        raise ConfigurationError(
            f"Missing required configuration value: {name}. "
            f"Pass it directly or set {prefix}{name}."
        )
    return value.strip()


def _float_value(
    explicit: Optional[float],
    environment: Mapping[str, str],
    prefix: str,
    name: str,
    default: float,
) -> float:
    raw = explicit
    if raw is None:
        raw = _environment_value(environment, prefix, name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{prefix}{name} must be a number.") from exc
    if value <= 0:
        raise ConfigurationError(f"{prefix}{name} must be greater than zero.")
    return value


def _int_value(
    explicit: Optional[int],
    environment: Mapping[str, str],
    prefix: str,
    name: str,
    default: int,
) -> int:
    raw = explicit
    if raw is None:
        raw = _environment_value(environment, prefix, name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{prefix}{name} must be an integer.") from exc
    if value < 0:
        raise ConfigurationError(f"{prefix}{name} cannot be negative.")
    return value


@dataclass(frozen=True)
class VersionBeaconConfig:
    """Validated configuration used by :class:`VersionChecker`."""

    app_name: str
    current_version: str
    version_url: str
    timeout: float = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES
    user_agent: str = DEFAULT_USER_AGENT

    def __post_init__(self) -> None:
        if not self.app_name.strip():
            raise ConfigurationError("app_name cannot be empty.")
        if not self.current_version.strip():
            raise ConfigurationError("current_version cannot be empty.")
        if not self.version_url.strip():
            raise ConfigurationError("version_url cannot be empty.")

        parsed = urlparse(self.version_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConfigurationError(
                "version_url must be an absolute HTTP or HTTPS URL."
            )
        if self.timeout <= 0:
            raise ConfigurationError("timeout must be greater than zero.")
        if self.retries < 0:
            raise ConfigurationError("retries cannot be negative.")
        if self.max_response_bytes <= 0:
            raise ConfigurationError("max_response_bytes must be greater than zero.")

    @classmethod
    def from_env(
        cls,
        prefix: str = DEFAULT_ENV_PREFIX,
        *,
        environment: Optional[Mapping[str, str]] = None,
    ) -> "VersionBeaconConfig":
        """Create configuration from environment variables."""

        return cls.from_sources(prefix=prefix, environment=environment)

    @classmethod
    def from_sources(
        cls,
        *,
        app_name: Optional[str] = None,
        current_version: Optional[str] = None,
        version_url: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        max_response_bytes: Optional[int] = None,
        user_agent: Optional[str] = None,
        prefix: str = DEFAULT_ENV_PREFIX,
        environment: Optional[Mapping[str, str]] = None,
    ) -> "VersionBeaconConfig":
        """Resolve explicit values first, then environment variables."""

        env = os.environ if environment is None else environment
        resolved_user_agent = user_agent
        if resolved_user_agent is None:
            resolved_user_agent = _environment_value(env, prefix, "USER_AGENT")
        if resolved_user_agent is None:
            resolved_user_agent = DEFAULT_USER_AGENT

        return cls(
            app_name=_required_value(app_name, env, prefix, "APP_NAME"),
            current_version=_required_value(
                current_version, env, prefix, "CURRENT_VERSION"
            ),
            version_url=_required_value(version_url, env, prefix, "VERSION_URL"),
            timeout=_float_value(timeout, env, prefix, "TIMEOUT", DEFAULT_TIMEOUT),
            retries=_int_value(retries, env, prefix, "RETRIES", DEFAULT_RETRIES),
            max_response_bytes=_int_value(
                max_response_bytes,
                env,
                prefix,
                "MAX_RESPONSE_BYTES",
                DEFAULT_MAX_RESPONSE_BYTES,
            ),
            user_agent=resolved_user_agent,
        )
