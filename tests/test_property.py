"""Property-based tests using Hypothesis."""

from __future__ import annotations

import pandas as pd
from hypothesis import given, strategies as st

from timeseries_expand import ExpandConfig, FrequencyExpander
from timeseries_expand.frequencies import Frequency


@given(
    n_releases=st.integers(min_value=2, max_value=10),
    base_value=st.floats(min_value=10, max_value=1000, allow_nan=False),
    delta_days=st.integers(min_value=5, max_value=14),
)
def test_published_values_preserved(n_releases, base_value, delta_days):
    """After expansion, the value at each release timestamp must equal the original."""
    releases = pd.date_range("2024-01-01", periods=n_releases, freq=f"{delta_days}D")
    df = pd.DataFrame({"timestamp": releases, "value": base_value})

    cfg = ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY)
    result = FrequencyExpander().expand(df, cfg)

    expected_utc = releases.tz_localize("UTC")
    actual_set = set(result["timestamp"].tolist())
    for ts in expected_utc:
        assert ts in actual_set, f"missing row for {ts}"
        matched = result[result["timestamp"] == ts]
        assert matched["value"].iloc[0] == base_value


@given(
    n_releases=st.integers(min_value=2, max_value=8),
    base_value=st.floats(min_value=10, max_value=1000, allow_nan=False),
)
def test_no_extrapolation_beyond_last_release(n_releases, base_value):
    """The expanded series must not extend past the last release."""
    releases = pd.date_range("2024-06-01", periods=n_releases, freq="7D")
    df = pd.DataFrame({"timestamp": releases, "value": base_value})

    cfg = ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY)
    result = FrequencyExpander().expand(df, cfg)

    expected_max = releases[-1].tz_localize("UTC")
    actual_max = result["timestamp"].max()
    assert actual_max == expected_max, f"max {actual_max} != expected {expected_max}"
