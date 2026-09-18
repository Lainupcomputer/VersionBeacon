"""Exceptions raised by LUCS-UVC."""


class UVCError(Exception):
    """Base class for all LUCS-UVC errors."""


class ConfigurationError(UVCError, ValueError):
    """Raised when the checker configuration is missing or invalid."""


class InvalidVersionError(UVCError, ValueError):
    """Raised when a version is not supported by the version parser."""


class VersionFetchError(UVCError):
    """Raised when the version endpoint cannot be reached."""


class VersionResponseError(UVCError):
    """Raised when the version endpoint returns invalid data."""
