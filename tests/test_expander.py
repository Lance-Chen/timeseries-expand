"""Test suite for FrequencyExpander."""

from __future__ import annotations

import pandas as pd
import pytest

from timeseries_expand import ExpandConfig, FrequencyExpander
from timeseries_expand.frequencies import Frequency


@pytest.fixture
def expander() -> FrequencyExpander:
    return FrequencyExpander()


@pytest.fixture
def cfg_weekly_to_hourly() -> ExpandConfig:
    return ExpandConfig(
        source_freq=Frequency.WEEKLY,
        target_freq=Frequency.HOURLY,
    )


def _to_utc(ts):
    """Convert any timestamp-like to a UTC-aware Timestamp."""
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t


def _value_at(result, ts):
    """Look up the value in `result` at timestamp `ts` (UTC)."""
    target = _to_utc(ts)
    matched = result.loc[result["timestamp"] == target, "value"]
    assert not matched.empty, f"no row for {target}"
    return matched.iloc[0]


# ----------------- T01: normal consecutive weeks -----------------
def test_t01_normal_consecutive_weeks(expander, cfg_weekly_to_hourly):
    releases = pd.date_range("2024-01-01", periods=4, freq="7D")
    df = pd.DataFrame({"timestamp": releases, "value": [100.0, 101.0, 102.0, 103.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    # 4 releases spanning 21 days inclusive (2024-01-01 .. 2024-01-22)
    assert len(result) == 21 * 24 + 1
    assert result["value"].notna().all()
    assert result["gap_flag"].dtype == bool
    assert result["gap_flag"].sum() == 0
    # First release value at its timestamp
    assert _value_at(result, releases[0]) == 100.0
    # Value switches at second release timestamp
    assert _value_at(result, releases[1]) == 101.0
    # Value carried forward one hour before second release
    just_before = _to_utc(releases[1]) - pd.Timedelta(hours=1)
    assert _value_at(result, just_before) == 100.0


# ----------------- T02: holiday shifted 1 day -----------------
def test_t02_holiday_shifted_1_day(expander, cfg_weekly_to_hourly):
    releases = pd.to_datetime(
        ["2024-01-01", "2024-01-08", "2024-01-16", "2024-01-22"]  # 7,8,6 days
    )
    df = pd.DataFrame({"timestamp": releases, "value": [10.0, 20.0, 30.0, 40.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    for ts, expected in zip(releases, [10.0, 20.0, 30.0, 40.0]):
        assert _value_at(result, ts) == expected


# ----------------- T04: missing week (14-day gap) -----------------
def test_t04_missing_week(expander, cfg_weekly_to_hourly):
    releases = pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-22"])  # 14-day gap
    df = pd.DataFrame({"timestamp": releases, "value": [100.0, 101.0, 102.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    # 2024-01-08 to 2024-01-22 should be filled with 101.0
    mid = result[
        (result["timestamp"] >= _to_utc("2024-01-08"))
        & (result["timestamp"] < _to_utc("2024-01-22"))
    ]
    assert (mid["value"] == 101.0).all()
    # gap_flag should be True at the end of the gap (2024-01-22)
    gap_row = result.loc[result["timestamp"] == _to_utc("2024-01-22")]
    assert bool(gap_row["gap_flag"].iloc[0]) is True


# ----------------- T07: starting boundary -----------------
def test_t07_starting_boundary(expander, cfg_weekly_to_hourly):
    releases = pd.to_datetime(["2024-03-15"])
    df = pd.DataFrame({"timestamp": releases, "value": [500.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    # 24 hourly rows spanning 2024-03-15 (00:00 .. 23:00)
    assert result["timestamp"].min() == _to_utc("2024-03-15 00:00")
    assert result["timestamp"].max() == _to_utc("2024-03-15 23:00")
    assert len(result) == 24
    assert (result["value"] == 500.0).all()


# ----------------- T08: ending boundary -----------------
def test_t08_ending_boundary(expander, cfg_weekly_to_hourly):
    releases = pd.to_datetime(["2024-01-01", "2024-01-08"])
    df = pd.DataFrame({"timestamp": releases, "value": [100.0, 101.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    # Should not extrapolate past the last release
    assert result["timestamp"].max() == _to_utc("2024-01-08")


# ----------------- T09: cross year -----------------
def test_t09_cross_year(expander, cfg_weekly_to_hourly):
    releases = pd.to_datetime(["2023-12-25", "2024-01-01"])
    df = pd.DataFrame({"timestamp": releases, "value": [99.0, 100.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    # 2024-01-01 00:00 should switch to 100.0
    assert _value_at(result, "2024-01-01") == 100.0
    # 2023-12-31 23:00 should still be 99.0
    assert _value_at(result, "2023-12-31 23:00") == 99.0


# ----------------- T15: NaT dropped -----------------
def test_t15_nat_timestamp_dropped(expander, cfg_weekly_to_hourly):
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2024-01-01", None, "2024-01-08"], utc=True
            ),
            "value": [100.0, 200.0, 101.0],
        }
    )

    result = expander.expand(df, cfg_weekly_to_hourly)

    # NaT row should be dropped before reindexing
    assert result["timestamp"].notna().all()
    # No rows for value=200 (it was on NaT row)
    assert (result["value"] != 200.0).all()


# ----------------- T14: duplicate timestamps -----------------
def test_t14_duplicate_timestamps(expander, cfg_weekly_to_hourly):
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2024-01-01", "2024-01-01", "2024-01-08"], utc=True
            ),
            "value": [100.0, 999.0, 101.0],
        }
    )

    result = expander.expand(df, cfg_weekly_to_hourly)

    # Last duplicate value (999.0) should win
    assert _value_at(result, "2024-01-01") == 999.0


# ----------------- Input validation -----------------
def test_missing_columns_raises(expander, cfg_weekly_to_hourly):
    bad = pd.DataFrame({"date": [1, 2], "price": [3, 4]})
    with pytest.raises(KeyError):
        expander.expand(bad, cfg_weekly_to_hourly, time_col="timestamp")


# ----------------- Frequency.parse -----------------
def test_frequency_parse():
    assert Frequency.parse("h") == Frequency.HOURLY
    assert Frequency.parse(Frequency.YEARLY) == Frequency.YEARLY
    with pytest.raises(ValueError):
        Frequency.parse("not-a-frequency")


# ----------------- Performance smoke test (slow marker) -----------------
@pytest.mark.slow
def test_t20_30_years_weekly_to_hourly_runs_under_10s(expander):
    releases = pd.date_range("1990-01-01", periods=52 * 30, freq="7D")
    values = [100.0 + i * 0.1 for i in range(len(releases))]
    df = pd.DataFrame({"timestamp": releases, "value": values})

    import time

    start = time.perf_counter()
    cfg = ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY)
    result = expander.expand(df, cfg)
    elapsed = time.perf_counter() - start

    assert elapsed < 10.0, f"took {elapsed:.2f}s, expected < 10s"
    assert len(result) > 200_000
