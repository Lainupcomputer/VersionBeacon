"""Version parsing and comparison utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering
from typing import Tuple, Union

from .exceptions import InvalidVersionError


_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?$")


@total_ordering
@dataclass(frozen=True)
class Version:
    """A normalized three- or four-part numeric version.

    Three-part versions are normalized with a trailing zero, so ``1.2.3``
    and ``1.2.3.0`` compare as equal.
    """

    original: str
    parts: Tuple[int, int, int, int]

    def __str__(self) -> str:
        return self.original

    def __repr__(self) -> str:
        return f"Version('{self.original}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.parts == other.parts

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.parts < other.parts


def parse_version(value: Union[str, Version]) -> Version:
    """Parse a supported version string.

    Supported formats are ``MAJOR.MINOR.PATCH`` and
    ``MAJOR.MINOR.PATCH.FIX``. Components must be non-negative integers.
    """

    if isinstance(value, Version):
        return value

    if not isinstance(value, str):
        raise InvalidVersionError("Version must be a string.")

    normalized = value.strip()
    match = _VERSION_PATTERN.fullmatch(normalized)
    if match is None:
        raise InvalidVersionError(
            f"Invalid version '{value}'. Expected MAJOR.MINOR.PATCH "
            "or MAJOR.MINOR.PATCH.FIX."
        )

    numbers = tuple(int(part) for part in match.groups() if part is not None)
    parts = numbers + (0,) if len(numbers) == 3 else numbers
    return Version(original=normalized, parts=parts)  # type: ignore[arg-type]
