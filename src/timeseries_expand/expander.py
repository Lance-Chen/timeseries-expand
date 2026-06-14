"""Core FrequencyExpander implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

import pandas as pd

from timeseries_expand.frequencies import Frequency


@dataclass
class ExpandConfig:
    """Configuration for a frequency-expansion operation."""

    source_freq: Frequency | str
    target_freq: Frequency | str
    timezone: str = "UTC"
    """Timezone of the resulting timestamps. Internally we work in UTC."""
    gap_threshold_multiplier: float = 1.5
    """Multiples of `expected_days` above which a gap is flagged."""

    def __post_init__(self) -> None:
        self.source_freq = Frequency.parse(self.source_freq)
        self.target_freq = Frequency.parse(self.target_freq)


class FrequencyExpander:
    """Registry-based time-series frequency expander.

    Expands a sparse low-frequency series into a dense high-frequency series
    by carrying each published value forward until the next publication
    (publication-aware forward fill, semantics `[T, T_next)`).

    Internally all timestamps are normalized to UTC for deterministic DST
    handling; the result is converted to `cfg.timezone` on output.
    """

    def expand(
        self,
        df: pd.DataFrame,
        cfg: ExpandConfig,
        time_col: str = "timestamp",
        value_col: str = "value",
        how: Literal["ffill", "nearest"] = "ffill",
    ) -> pd.DataFrame:
        if how != "ffill":
            raise NotImplementedError(f"fill strategy {how!r} not implemented")

        # cfg.source_freq/target_freq are narrowed to Frequency in __post_init__,
        # but mypy doesn't track that. Cast explicitly.
        target = cast(Frequency, cfg.target_freq)
        source = cast(Frequency, cfg.source_freq)

        df = self._validate_input(df, time_col, value_col)

        start_ts = df[time_col].min()
        end_ts = df[time_col].max()

        # Build target index in UTC (DST-safe).
        if start_ts == end_ts:
            periods = _default_window(target)
            idx_utc = pd.date_range(
                start=start_ts,
                periods=periods,
                freq=target.value,
                tz="UTC",
            )
        else:
            idx_utc = pd.date_range(
                start=start_ts,
                end=end_ts,
                freq=target.value,
                tz="UTC",
            )

        # Ensure every source timestamp is represented in the target index.
        source_idx = pd.DatetimeIndex(df[time_col].unique())
        idx_utc = idx_utc.union(source_idx).sort_values()

        result = (
            df.set_index(time_col)
            .reindex(idx_utc)
            .ffill()
            .reset_index()
            .rename(columns={"index": time_col})
        )

        # Gap detection (UTC).
        gap_flags = self._detect_gaps(df, source, time_col, cfg.gap_threshold_multiplier)
        gap_idx = pd.DatetimeIndex(gap_flags.index[gap_flags])
        if len(gap_idx) > 0:
            if gap_idx.tz is None:
                gap_idx = gap_idx.tz_localize("UTC")
            else:
                gap_idx = gap_idx.tz_convert("UTC")
            result["gap_flag"] = result[time_col].isin(gap_idx)
        else:
            result["gap_flag"] = False

        result = result.dropna(subset=[value_col]).reset_index(drop=True)

        # Convert to requested display timezone.
        if cfg.timezone != "UTC":
            result[time_col] = result[time_col].dt.tz_convert(cfg.timezone)

        return result

    @staticmethod
    def _validate_input(df: pd.DataFrame, time_col: str, value_col: str) -> pd.DataFrame:
        if time_col not in df.columns or value_col not in df.columns:
            raise KeyError(
                f"Input must contain columns {time_col!r} and {value_col!r}; got {list(df.columns)}"
            )
        out = df[[time_col, value_col]].copy()
        out = out.loc[out[time_col].notna()]
        out = out.drop_duplicates(subset=[time_col], keep="last")  # type: ignore[call-overload]
        out[time_col] = pd.to_datetime(out[time_col], utc=True)
        out = out.sort_values(time_col).reset_index(drop=True)  # type: ignore[call-overload]
        return out  # type: ignore[return-value]

    @staticmethod
    def _detect_gaps(
        df: pd.DataFrame,
        source: Frequency,
        time_col: str,
        threshold_multiplier: float = 1.5,
    ) -> pd.Series:
        threshold_days = source.expected_days * threshold_multiplier
        ts_series = df[time_col]
        delta_seconds = ts_series.diff().dt.total_seconds()  # type: ignore[arg-type]
        threshold_seconds = threshold_days * 86400.0
        bool_list = []
        for v in delta_seconds:
            try:
                bool_list.append(float(v) > threshold_seconds)
            except (TypeError, ValueError):
                bool_list.append(False)
        flags = pd.Series(bool_list, index=df[time_col].values)
        return flags


def _default_window(target: Frequency) -> int:
    """Default number of periods to expand a single-release series."""
    table = {
        Frequency.YEARLY: 2,
        Frequency.QUARTERLY: 4,
        Frequency.MONTHLY: 2,
        Frequency.SEMI_MONTHLY: 2,
        Frequency.WEEKLY: 7,
        Frequency.DAILY: 24,
        Frequency.HOURLY: 24,
    }
    return table[target]
