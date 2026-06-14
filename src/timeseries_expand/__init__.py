"""timeseries-expand: publication-aware time-series frequency expansion."""

from __future__ import annotations

import pandas as pd

from timeseries_expand.expander import ExpandConfig, FrequencyExpander
from timeseries_expand.frequencies import Frequency

__version__ = "0.1.0"
__all__ = ["FrequencyExpander", "ExpandConfig", "Frequency", "expand"]


def expand(
    df: pd.DataFrame,
    source_freq: str | Frequency,
    target_freq: str | Frequency,
    *,
    timezone: str = "UTC",
    gap_threshold_multiplier: float = 1.5,
    time_col: str = "timestamp",
    value_col: str = "value",
) -> pd.DataFrame:
    """Expand a low-frequency time series to a higher frequency.

    Convenience wrapper around :class:`FrequencyExpander` for one-shot use.

    Args:
        df: Input DataFrame with [time_col, value_col] columns.
        source_freq: Source frequency alias (``"YE"``, ``"QE"``, ``"ME"``,
            ``"SME"``, ``"W-MON"``, ``"D"``, ``"h"``) or a :class:`Frequency`.
        target_freq: Target frequency (must be strictly higher than source).
        timezone: Output timezone. Internally UTC for DST safety.
        gap_threshold_multiplier: Gaps exceeding this multiple of
            ``expected_days`` are flagged in the ``gap_flag`` column.
        time_col: Name of the timestamp column.
        value_col: Name of the value column.

    Returns:
        DataFrame with ``[timestamp, value, gap_flag]`` columns.

    Example:
        >>> import pandas as pd
        >>> from timeseries_expand import expand
        >>> df = pd.DataFrame({
        ...     "timestamp": pd.to_datetime(["2024-01-01", "2024-01-08"]),
        ...     "value": [100.0, 101.0],
        ... })
        >>> result = expand(df, "W-MON", "h")
    """
    cfg = ExpandConfig(
        source_freq=source_freq,
        target_freq=target_freq,
        timezone=timezone,
        gap_threshold_multiplier=gap_threshold_multiplier,
    )
    return FrequencyExpander().expand(df, cfg, time_col=time_col, value_col=value_col)
