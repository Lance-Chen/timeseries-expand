"""Edge-case tests covering boundary, holiday, DST, and data-quality scenarios."""

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
    return ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY)


def _to_utc(ts):
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t


def _value_at(result, ts):
    target = _to_utc(ts)
    matched = result.loc[result["timestamp"] == target, "value"]
    assert not matched.empty, f"no row for {target}"
    return matched.iloc[0]


# ----------------- T03: holiday shifted 2 days (9-day gap, still under 10.5 day threshold) -----------------
def test_t03_holiday_shifted_2_days(expander, cfg_weekly_to_hourly):
    releases = pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-17"])  # 7, 9 days
    df = pd.DataFrame({"timestamp": releases, "value": [100.0, 101.0, 102.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    for ts, expected in zip(releases, [100.0, 101.0, 102.0]):
        assert _value_at(result, ts) == expected


# ----------------- T05: missing 2 weeks (21-day gap) -----------------
def test_t05_missing_two_weeks(expander, cfg_weekly_to_hourly):
    releases = pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-29"])  # 21-day gap
    df = pd.DataFrame({"timestamp": releases, "value": [100.0, 101.0, 102.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    # Whole period from 2024-01-08 to 2024-01-29 should be filled with 101.0
    mid = result[
        (result["timestamp"] >= _to_utc("2024-01-08"))
        & (result["timestamp"] < _to_utc("2024-01-29"))
    ]
    assert (mid["value"] == 101.0).all()
    # gap_flag should mark the end of the gap
    gap_row = result.loc[result["timestamp"] == _to_utc("2024-01-29")]
    assert bool(gap_row["gap_flag"].iloc[0]) is True


# ----------------- T06: extreme gap (60 days) -----------------
def test_t06_extreme_gap_does_not_crash(expander, cfg_weekly_to_hourly):
    releases = pd.to_datetime(["2024-01-01", "2024-01-08", "2024-03-08"])  # 60-day gap
    df = pd.DataFrame({"timestamp": releases, "value": [100.0, 101.0, 102.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    assert len(result) > 0
    assert result["value"].notna().all()
    gap_row = result.loc[result["timestamp"] == _to_utc("2024-03-08")]
    assert bool(gap_row["gap_flag"].iloc[0]) is True


# ----------------- T10: cross month (D target) -----------------
def test_t10_cross_month_boundary_daily(expander):
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-30", "2024-02-05"]),
        "value": [100.0, 200.0],
    })
    cfg = ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.DAILY)
    result = expander.expand(df, cfg)

    # Jan 31 should carry 100; Feb 1-4 should also carry 100
    assert _value_at(result, "2024-01-31") == 100.0
    for ts in ["2024-02-01", "2024-02-02", "2024-02-04"]:
        assert _value_at(result, ts) == 100.0
    # Feb 5 switches to 200
    assert _value_at(result, "2024-02-05") == 200.0


# ----------------- T11: DST spring forward (US Eastern) -----------------
def test_t11_dst_spring_forward_safe_in_utc(expander):
    """DST handling: as long as we work in UTC, no rows are lost or duplicated."""
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-03-08", "2024-03-15"]),  # US DST
        "value": [100.0, 101.0],
    })
    cfg = ExpandConfig(
        source_freq=Frequency.WEEKLY,
        target_freq=Frequency.HOURLY,
        timezone="UTC",
    )
    result = expander.expand(df, cfg)

    # No NaN, no error, value switches at the next weekly release
    assert result["value"].notna().all()
    assert _value_at(result, "2024-03-08") == 100.0
    assert _value_at(result, "2024-03-15") == 101.0


# ----------------- T12: DST fall back (US Eastern) -----------------
def test_t12_dst_fall_back_safe_in_utc(expander):
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-11-01", "2024-11-08"]),
        "value": [100.0, 101.0],
    })
    cfg = ExpandConfig(
        source_freq=Frequency.WEEKLY,
        target_freq=Frequency.HOURLY,
        timezone="UTC",
    )
    result = expander.expand(df, cfg)

    assert result["value"].notna().all()
    assert _value_at(result, "2024-11-01") == 100.0
    assert _value_at(result, "2024-11-08") == 101.0


# ----------------- T13: holiday shift to non-Monday publication -----------------
def test_t13_publication_on_wednesday(expander, cfg_weekly_to_hourly):
    """Real-world: weekly release published on Wednesday due to Monday holiday."""
    releases = pd.to_datetime([
        "2024-01-01",  # Mon
        "2024-01-10",  # Wed (delayed from Jan 8 Mon)
        "2024-01-15",  # Mon
        "2024-01-22",  # Mon
    ])
    df = pd.DataFrame({"timestamp": releases, "value": [100.0, 101.0, 102.0, 103.0]})

    result = expander.expand(df, cfg_weekly_to_hourly)

    for ts, expected in zip(releases, [100.0, 101.0, 102.0, 103.0]):
        assert _value_at(result, ts) == expected


# ----------------- T16: NaN value (defensive behavior) -----------------
def test_t16_nan_value_in_source(expander, cfg_weekly_to_hourly):
    """If a source value is NaN, ffill will propagate the previous non-NaN value."""
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
        "value": [100.0, float("nan"), 102.0],
    })
    cfg = ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY)
    result = expander.expand(df, cfg)

    # All result rows should have a value (NaN was ffill'd from previous)
    assert result["value"].notna().all()
    # After the NaN source, the row at 2024-01-08 carries the previous (100.0)
    assert _value_at(result, "2024-01-08") == 100.0


# ----------------- T17: negative / extreme value -----------------
def test_t17_extreme_values_preserved(expander, cfg_weekly_to_hourly):
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-08"]),
        "value": [-100.5, 0.0],
    })
    cfg = ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY)
    result = expander.expand(df, cfg)

    assert _value_at(result, "2024-01-01") == -100.5
    assert _value_at(result, "2024-01-07 23:00") == -100.5
    assert _value_at(result, "2024-01-08") == 0.0


# ----------------- T18: empty input -----------------
def test_t18_empty_input_raises(expander, cfg_weekly_to_hourly):
    df = pd.DataFrame({"timestamp": pd.to_datetime([]), "value": []})
    with pytest.raises((KeyError, ValueError)):
        expander.expand(df, cfg_weekly_to_hourly)


# ----------------- T19: monthly frequency crossing year boundary -----------------
def test_t19_monthly_across_year_boundary(expander):
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2023-11-30", "2023-12-31", "2024-01-31"]),
        "value": [100.0, 200.0, 300.0],
    })
    cfg = ExpandConfig(source_freq=Frequency.MONTHLY, target_freq=Frequency.DAILY)
    result = expander.expand(df, cfg)

    assert _value_at(result, "2023-12-15") == 100.0
    assert _value_at(result, "2023-12-31") == 200.0
    assert _value_at(result, "2024-01-15") == 200.0
    assert _value_at(result, "2024-01-31") == 300.0


# ----------------- Bonus: gap_threshold_multiplier configuration -----------------
def test_gap_threshold_multiplier_configurable(expander):
    """A multiplier of 2.0 should only flag gaps exceeding 2x expected cadence."""
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-22"]),  # 14-day gap
        "value": [100.0, 101.0, 102.0],
    })
    cfg_default = ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY)  # 1.5x = 10.5
    cfg_strict = ExpandConfig(
        source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY, gap_threshold_multiplier=2.0
    )  # 2.0x = 14.0

    result_default = expander.expand(df, cfg_default)
    result_strict = expander.expand(df, cfg_strict)

    # 14-day gap > 10.5 -> flagged by default; NOT > 14.0 -> not flagged by strict
    default_gap_count = result_default["gap_flag"].sum()
    strict_gap_count = result_strict["gap_flag"].sum()

    assert default_gap_count >= 1
    assert strict_gap_count == 0


# ----------------- Bonus: timezone parameter is respected -----------------
def test_timezone_parameter_respected(expander):
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-08"]),
        "value": [100.0, 101.0],
    })
    cfg = ExpandConfig(
        source_freq=Frequency.WEEKLY,
        target_freq=Frequency.HOURLY,
        timezone="Asia/Shanghai",
    )
    result = expander.expand(df, cfg)
    assert result["timestamp"].dt.tz is not None
    # First timestamp should be in Asia/Shanghai timezone
    assert str(result["timestamp"].iloc[0].tz) == "Asia/Shanghai"
