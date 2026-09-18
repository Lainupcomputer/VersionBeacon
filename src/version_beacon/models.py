"""Public result and event payload models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class CheckStatus(str, Enum):
    """Possible outcomes of a version check."""

    UP_TO_DATE = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    CURRENT_AHEAD = "current_ahead"
    FAILED = "failed"


@dataclass(frozen=True)
class CheckStarted:
    """Payload emitted when a check starts."""

    app_name: str
    current_version: str
    started_at: datetime


@dataclass(frozen=True)
class CheckResult:
    """The complete result of a version check."""

    app_name: str
    current_version: str
    latest_version: Optional[str]
    status: CheckStatus
    checked_at: datetime
    version_url: str
    release_url: Optional[str] = None
    release_notes: Optional[str] = None
    error: Optional[str] = None

    @property
    def update_available(self) -> bool:
        """Whether a newer version is available."""

        return self.status is CheckStatus.UPDATE_AVAILABLE

    @property
    def up_to_date(self) -> bool:
        """Whether the installed version is current."""

        return self.status is CheckStatus.UP_TO_DATE

    @property
    def failed(self) -> bool:
        """Whether the check failed."""

        return self.status is CheckStatus.FAILED

    @property
    def current_is_ahead(self) -> bool:
        """Whether the local version is newer than the remote version."""

        return self.status is CheckStatus.CURRENT_AHEAD
