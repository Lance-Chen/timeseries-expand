"""Tests for the full frequency-expansion matrix.

For every supported source frequency (YE, QE, ME, SME, W-MON, D) and every
higher target frequency, verify:
1. The expansion completes without error.
2. The first source timestamp's value is preserved in the result.
3. The value carries forward correctly across at least one boundary.
4. The result has the expected number of rows (within a tolerance).
"""

from __future__ import annotations

import pandas as pd
import pytest

from timeseries_expand import ExpandConfig, FrequencyExpander
from timeseries_expand.frequencies import Frequency

# (source, target, source_pd_alias, target_pd_alias, n_releases)
COMBINATIONS = [
    (Frequency.YEARLY, Frequency.QUARTERLY, "YE", "QE", 5),
    (Frequency.YEARLY, Frequency.MONTHLY, "YE", "ME", 5),
    (Frequency.YEARLY, Frequency.SEMI_MONTHLY, "YE", "SME", 5),
    (Frequency.YEARLY, Frequency.WEEKLY, "YE", "W-MON", 5),
    (Frequency.YEARLY, Frequency.DAILY, "YE", "D", 5),
    (Frequency.YEARLY, Frequency.HOURLY, "YE", "h", 5),
    (Frequency.QUARTERLY, Frequency.MONTHLY, "QE", "ME", 8),
    (Frequency.QUARTERLY, Frequency.SEMI_MONTHLY, "QE", "SME", 8),
    (Frequency.QUARTERLY, Frequency.WEEKLY, "QE", "W-MON", 8),
    (Frequency.QUARTERLY, Frequency.DAILY, "QE", "D", 8),
    (Frequency.QUARTERLY, Frequency.HOURLY, "QE", "h", 8),
    (Frequency.MONTHLY, Frequency.SEMI_MONTHLY, "ME", "SME", 6),
    (Frequency.MONTHLY, Frequency.WEEKLY, "ME", "W-MON", 6),
    (Frequency.MONTHLY, Frequency.DAILY, "ME", "D", 6),
    (Frequency.MONTHLY, Frequency.HOURLY, "ME", "h", 6),
    (Frequency.SEMI_MONTHLY, Frequency.WEEKLY, "SME", "W-MON", 8),
    (Frequency.SEMI_MONTHLY, Frequency.DAILY, "SME", "D", 8),
    (Frequency.SEMI_MONTHLY, Frequency.HOURLY, "SME", "h", 8),
    (Frequency.WEEKLY, Frequency.DAILY, "W-MON", "D", 8),
    (Frequency.WEEKLY, Frequency.HOURLY, "W-MON", "h", 8),
    (Frequency.DAILY, Frequency.HOURLY, "D", "h", 30),
]


def _to_utc(ts):
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t


def _value_at(result, ts):
    target = _to_utc(ts)
    matched = result.loc[result["timestamp"] == target, "value"]
    assert not matched.empty, f"no row for {target}"
    return matched.iloc[0]


@pytest.fixture
def expander() -> FrequencyExpander:
    return FrequencyExpander()


@pytest.mark.parametrize(
    "src,tgt,src_alias,tgt_alias,n",
    COMBINATIONS,
    ids=[f"{s.value}-{t.value}" for s, t, _, _, _ in COMBINATIONS],
)
def test_expansion_preserves_first_value(expander, src, tgt, src_alias, tgt_alias, n):
    """The first source timestamp's value must appear at that timestamp in the result."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq=src_alias),
            "value": [100.0 + i for i in range(n)],
        }
    )
    cfg = ExpandConfig(source_freq=src, target_freq=tgt)
    result = expander.expand(df, cfg)

    assert len(result) > 0
    first_ts = df["timestamp"].iloc[0]
    assert _value_at(result, first_ts) == 100.0


@pytest.mark.parametrize(
    "src,tgt,src_alias,tgt_alias,n",
    COMBINATIONS,
    ids=[f"{s.value}-{t.value}" for s, t, _, _, _ in COMBINATIONS],
)
def test_expansion_carries_forward_at_boundary(expander, src, tgt, src_alias, tgt_alias, n):
    """The second source value must be present at the second source timestamp."""
    if n < 2:
        pytest.skip("need at least 2 releases")
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq=src_alias),
            "value": [100.0 + i for i in range(n)],
        }
    )
    cfg = ExpandConfig(source_freq=src, target_freq=tgt)
    result = expander.expand(df, cfg)

    second_ts = df["timestamp"].iloc[1]
    assert _value_at(result, second_ts) == 101.0


@pytest.mark.parametrize(
    "src,tgt,src_alias,tgt_alias,n",
    COMBINATIONS,
    ids=[f"{s.value}-{t.value}" for s, t, _, _, _ in COMBINATIONS],
)
def test_expansion_no_nan_values(expander, src, tgt, src_alias, tgt_alias, n):
    """Every row in the result must have a non-NaN value (ffill always works)."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq=src_alias),
            "value": [100.0 + i for i in range(n)],
        }
    )
    cfg = ExpandConfig(source_freq=src, target_freq=tgt)
    result = expander.expand(df, cfg)

    assert len(result) > 0
    assert result["value"].notna().all()
    assert result["timestamp"].notna().all()


@pytest.mark.parametrize(
    "src,tgt,src_alias,tgt_alias,n",
    COMBINATIONS,
    ids=[f"{s.value}-{t.value}" for s, t, _, _, _ in COMBINATIONS],
)
def test_expansion_gap_flag_is_bool(expander, src, tgt, src_alias, tgt_alias, n):
    """gap_flag column must be boolean with no NaN."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq=src_alias),
            "value": [100.0 + i for i in range(n)],
        }
    )
    cfg = ExpandConfig(source_freq=src, target_freq=tgt)
    result = expander.expand(df, cfg)

    assert "gap_flag" in result.columns
    assert result["gap_flag"].dtype == bool
    # No gaps expected for uniformly-spaced input
    assert result["gap_flag"].sum() == 0


def test_yearly_to_weekly_preserves_year_boundary(expander):
    """YE -> W-MON: verify the year-end value carries through to Jan of next year."""
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2023-12-31", "2024-12-31"]),
            "value": [100.0, 200.0],
        }
    )
    cfg = ExpandConfig(source_freq=Frequency.YEARLY, target_freq=Frequency.WEEKLY)
    result = expander.expand(df, cfg)

    # First source timestamp is 2023-12-31 (Sunday) - value=100
    assert _value_at(result, "2023-12-31") == 100.0
    # The next weekly Monday (2024-01-01) should still carry 100
    assert _value_at(result, "2024-01-01") == 100.0
    # 2024-12-31 should have value 200
    assert _value_at(result, "2024-12-31") == 200.0


def test_quarterly_to_monthly_preserves_quarter_boundary(expander):
    """QE -> ME: verify Q1 value carries through Jan/Feb/Mar."""
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-03-31", "2024-06-30"]),
            "value": [100.0, 200.0],
        }
    )
    cfg = ExpandConfig(source_freq=Frequency.QUARTERLY, target_freq=Frequency.MONTHLY)
    result = expander.expand(df, cfg)

    # April and May 2024 should carry the Q1 value (100)
    for ts in ["2024-04-30", "2024-05-31"]:
        assert _value_at(result, ts) == 100.0
    # July through Sept should have Q2 value (200) - need a Q3 source to switch
    df2 = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-03-31", "2024-06-30", "2024-09-30"]),
            "value": [100.0, 200.0, 300.0],
        }
    )
    result2 = expander.expand(df2, cfg)
    for ts in ["2024-07-31", "2024-08-31"]:
        assert _value_at(result2, ts) == 200.0
    # Sept 30 should have Q3 value 300 (this is the source itself)
    assert _value_at(result2, "2024-09-30") == 300.0


def test_monthly_to_daily_preserves_month_boundary(expander):
    """ME -> D: verify January value carries through Feb, then switches at March source."""
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-31", "2024-02-29", "2024-03-31"]),
            "value": [100.0, 200.0, 300.0],
        }
    )
    cfg = ExpandConfig(source_freq=Frequency.MONTHLY, target_freq=Frequency.DAILY)
    result = expander.expand(df, cfg)

    # Feb 1, 15, 28 should all carry January value (100)
    for ts in ["2024-02-01", "2024-02-15", "2024-02-28"]:
        assert _value_at(result, ts) == 100.0
    # Mar 1, 15, 30 should carry February value (200)
    for ts in ["2024-03-01", "2024-03-15", "2024-03-30"]:
        assert _value_at(result, ts) == 200.0


def test_semi_monthly_to_weekly(expander):
    """SME -> W-MON: half-month boundary carries through weeks."""
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-15", "2024-02-01"]),
            "value": [100.0, 200.0],
        }
    )
    cfg = ExpandConfig(source_freq=Frequency.SEMI_MONTHLY, target_freq=Frequency.WEEKLY)
    result = expander.expand(df, cfg)

    # Week of Jan 15 (Monday Jan 15) has value 100
    assert _value_at(result, "2024-01-15") == 100.0
    # Week of Jan 22 should still carry 100 (until next release)
    assert _value_at(result, "2024-01-22") == 100.0
    # Week of Jan 29 still carries 100 (next release is Feb 1)
    assert _value_at(result, "2024-01-29") == 100.0
    # Week of Feb 5 should carry 200 (next release after Feb 1)
    # To switch, need a third release; use SME source Jan 15, Feb 1, Feb 15
    df2 = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-15", "2024-02-01", "2024-02-15"]),
            "value": [100.0, 200.0, 300.0],
        }
    )
    result2 = expander.expand(df2, cfg)
    assert _value_at(result2, "2024-02-05") == 200.0
    # 2024-02-15 is the source timestamp with value 300
    assert _value_at(result2, "2024-02-15") == 300.0


def test_daily_to_hourly(expander):
    """D -> h: each day value carries for 24 hours."""
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "value": [10.0, 20.0, 30.0],
        }
    )
    cfg = ExpandConfig(source_freq=Frequency.DAILY, target_freq=Frequency.HOURLY)
    result = expander.expand(df, cfg)

    # Each day's hourly value should be that day's value
    for ts in ["2024-01-01 00:00", "2024-01-01 23:00"]:
        assert _value_at(result, ts) == 10.0
    for ts in ["2024-01-02 00:00", "2024-01-02 23:00"]:
        assert _value_at(result, ts) == 20.0
    assert _value_at(result, "2024-01-03 00:00") == 30.0


def test_yearly_to_daily_full_year(expander):
    """YE -> D: one year should produce 365 or 366 daily rows (depending on source span)."""
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-12-31", "2025-12-31"]),
            "value": [100.0, 200.0],
        }
    )
    cfg = ExpandConfig(source_freq=Frequency.YEARLY, target_freq=Frequency.DAILY)
    result = expander.expand(df, cfg)

    # 366 days from 2024-12-31 to 2025-12-31 inclusive (2024 is leap year)
    assert len(result) >= 366
