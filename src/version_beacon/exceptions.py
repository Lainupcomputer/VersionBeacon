"""Exceptions raised by VersionBeacon."""


class VersionBeaconError(Exception):
    """Base class for all VersionBeacon errors."""


class ConfigurationError(VersionBeaconError, ValueError):
    """Raised when the checker configuration is missing or invalid."""


class InvalidVersionError(VersionBeaconError, ValueError):
    """Raised when a version is not supported by the version parser."""


class VersionFetchError(VersionBeaconError):
    """Raised when the version endpoint cannot be reached."""


class VersionResponseError(VersionBeaconError):
    """Raised when the version endpoint returns invalid data."""
