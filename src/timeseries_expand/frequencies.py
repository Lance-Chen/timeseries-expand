"""Frequency enum and registry for time-series expansion."""

from __future__ import annotations

from enum import Enum


class Frequency(str, Enum):
    """Supported source/target frequencies (pandas 2.2+ aliases)."""

    YEARLY = "YE"
    QUARTERLY = "QE"
    MONTHLY = "ME"
    SEMI_MONTHLY = "SME"
    WEEKLY = "W-MON"
    DAILY = "D"
    HOURLY = "h"

    @property
    def expected_days(self) -> int:
        """Expected number of days between consecutive publications."""
        return {
            Frequency.YEARLY: 366,
            Frequency.QUARTERLY: 92,
            Frequency.MONTHLY: 31,
            Frequency.SEMI_MONTHLY: 15,
            Frequency.WEEKLY: 7,
            Frequency.DAILY: 1,
            Frequency.HOURLY: 1,
        }[self]

    @classmethod
    def parse(cls, value: str | Frequency) -> Frequency:
        """Parse a string or Frequency into a Frequency enum value."""
        if isinstance(value, Frequency):
            return value
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(
                f"Unknown frequency: {value!r}. "
                f"Supported: {[f.value for f in cls]}"
            ) from exc