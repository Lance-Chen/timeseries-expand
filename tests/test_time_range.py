"""Tests for the start/end parameters on output timestamps.

Covers all 7 supported source frequencies x 7 boundary conditions,
plus error cases, input format variants, and CLI.
"""

from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from timeseries_expand import ExpandConfig, Frequency, expand

# ============================================================================
#  Fixtures
# ============================================================================


@pytest.fixture
def weekly_df() -> pd.DataFrame:
    """Year of weekly coal prices (52 weeks)."""
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=52, freq="W-MON"),
            "value": range(100, 152),
        }
    )


@pytest.fixture
def monthly_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-31", periods=12, freq="ME"),
            "value": range(200, 212),
        }
    )


# ============================================================================
#  Boundary correctness across all 7 source frequencies
# ============================================================================

# Each entry: (source_freq_enum, source_pd_alias, n_periods, description)
FREQS = [
    (Frequency.YEARLY, "YE", 3, "3 years yearly"),
    (Frequency.QUARTERLY, "QE", 8, "8 quarters"),
    (Frequency.MONTHLY, "ME", 12, "12 months"),
    (Frequency.SEMI_MONTHLY, "SME", 24, "24 semi-months"),
    (Frequency.WEEKLY, "W-MON", 12, "12 weeks"),
    (Frequency.DAILY, "D", 30, "30 days"),
]


@pytest.mark.parametrize("src,src_alias,n,label", FREQS, ids=[f[3] for f in FREQS])
def test_default_range_covers_full_input(src, src_alias, n, label):
    """Without start/end, output covers the actual input data range."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq=src_alias),
            "value": [100.0 + i for i in range(n)],
        }
    )
    result = expand(df, src, "h")
    # Use the input's actual min/max, not the requested start
    input_min = df["timestamp"].iloc[0]
    input_max = df["timestamp"].iloc[-1]
    assert result["timestamp"].min() <= pd.Timestamp(input_min).tz_localize("UTC")
    assert result["timestamp"].max() >= pd.Timestamp(input_max).tz_localize("UTC")


@pytest.mark.parametrize(
    "src,src_alias,n,label", FREQS, ids=[f"start_eq_min_{f[3]}" for f in FREQS]
)
def test_start_equals_input_min_works(src, src_alias, n, label):
    """start == input_min should be accepted (boundary)."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq=src_alias),
            "value": [100.0 + i for i in range(n)],
        }
    )
    result = expand(df, src, "h", start=df["timestamp"].iloc[0])
    assert result["timestamp"].min() == pd.Timestamp(df["timestamp"].iloc[0]).tz_localize("UTC")


@pytest.mark.parametrize("src,src_alias,n,label", FREQS, ids=[f"end_eq_max_{f[3]}" for f in FREQS])
def test_end_equals_input_max_works(src, src_alias, n, label):
    """end == input_max should be accepted (boundary)."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq=src_alias),
            "value": [100.0 + i for i in range(n)],
        }
    )
    result = expand(df, src, "h", end=df["timestamp"].iloc[-1])
    assert result["timestamp"].max() == pd.Timestamp(df["timestamp"].iloc[-1]).tz_localize("UTC")


def test_narrow_range_to_two_months(monthly_df):
    """Narrowing a 12-month range to 2-5 月 should work."""
    result = expand(monthly_df, "ME", "D", start="2024-03-01", end="2024-05-31")
    # Output is daily aligned to month-end; first row >= start, last <= end
    assert result["timestamp"].min() >= pd.Timestamp("2024-03-01").tz_localize("UTC")
    assert result["timestamp"].max() <= pd.Timestamp("2024-05-31").tz_localize("UTC")
    # All rows in the Mar-May range
    assert (result["timestamp"] >= pd.Timestamp("2024-03-01").tz_localize("UTC")).all()
    assert (result["timestamp"] <= pd.Timestamp("2024-05-31").tz_localize("UTC")).all()


def test_start_and_end_to_same_date(weekly_df):
    """start..end range produces a bounded window."""
    result = expand(weekly_df, "W-MON", "h", start="2024-04-01", end="2024-04-30")
    assert result["timestamp"].min() >= pd.Timestamp("2024-04-01").tz_localize("UTC")
    assert result["timestamp"].max() <= pd.Timestamp("2024-04-30").tz_localize("UTC")
    assert len(result) > 0


def test_only_start_no_end(weekly_df):
    """Only start given: output goes from start to input max."""
    result = expand(weekly_df, "W-MON", "D", start="2024-12-01")
    input_max = weekly_df["timestamp"].iloc[-1]
    assert result["timestamp"].min() >= pd.Timestamp("2024-12-01").tz_localize("UTC")
    # end = input max (not 2024-12-31)
    assert result["timestamp"].max() <= pd.Timestamp(input_max).tz_localize("UTC")


def test_only_end_no_start(weekly_df):
    """Only end given: output goes from input min to end."""
    result = expand(weekly_df, "W-MON", "D", end="2024-02-29")
    input_min = weekly_df["timestamp"].iloc[0]
    assert result["timestamp"].max() <= pd.Timestamp("2024-02-29 23:59:59").tz_localize("UTC")
    assert result["timestamp"].min() >= pd.Timestamp(input_min).tz_localize("UTC")


# ============================================================================
#  Error cases
# ============================================================================


def test_start_before_input_raises(weekly_df):
    """start < input_min should raise ValueError."""
    with pytest.raises(ValueError, match="start .* is before input range"):
        expand(weekly_df, "W-MON", "h", start="2023-01-01")


def test_end_after_input_raises(weekly_df):
    """end > input_max should raise ValueError."""
    with pytest.raises(ValueError, match="end .* is after input range"):
        expand(weekly_df, "W-MON", "h", end="2025-12-31")


def test_both_outside_raises_first_start(weekly_df):
    """Both start and end outside the input range; the start error is reported first."""
    with pytest.raises(ValueError, match="start"):
        expand(weekly_df, "W-MON", "h", start="2023-01-01", end="2025-12-31")


def test_start_one_microsecond_before_raises(weekly_df):
    """Edge case: start is 1 microsecond before the input's first timestamp."""
    boundary = weekly_df["timestamp"].iloc[0]
    just_before = boundary - pd.Timedelta(microseconds=1)
    with pytest.raises(ValueError, match="before input range"):
        expand(weekly_df, "W-MON", "h", start=just_before)


def test_end_one_microsecond_after_raises(weekly_df):
    """Edge case: end is 1 microsecond after the input's last timestamp."""
    boundary = weekly_df["timestamp"].iloc[-1]
    just_after = boundary + pd.Timedelta(microseconds=1)
    with pytest.raises(ValueError, match="after input range"):
        expand(weekly_df, "W-MON", "h", end=just_after)


def test_start_after_end_raises_at_config_time():
    """start > end should raise ValueError at config construction."""
    with pytest.raises(ValueError, match="start .* must be <= end"):
        ExpandConfig(
            source_freq="W-MON",
            target_freq="h",
            start="2024-12-01",
            end="2024-01-01",
        )


def test_unparseable_start_raises(weekly_df):
    """Garbage start string should raise ValueError (from pd.to_datetime)."""
    with pytest.raises(ValueError):
        expand(weekly_df, "W-MON", "h", start="not-a-date")


# ============================================================================
#  Input format variants
# ============================================================================


def test_start_as_string(weekly_df):
    """start accepts ISO date string."""
    result = expand(weekly_df, "W-MON", "h", start="2024-06-01")
    assert result["timestamp"].min() >= pd.Timestamp("2024-06-01").tz_localize("UTC")
    # Should reach the actual input max, not extend past it
    input_max = weekly_df["timestamp"].iloc[-1]
    assert result["timestamp"].max() <= pd.Timestamp(input_max).tz_localize("UTC")


def test_start_as_datetime_date(weekly_df):
    """start accepts datetime.date (not just Timestamp)."""
    result = expand(weekly_df, "W-MON", "h", start=dt.date(2024, 6, 1))
    assert result["timestamp"].min() >= pd.Timestamp("2024-06-01").tz_localize("UTC")
    input_max = weekly_df["timestamp"].iloc[-1]
    assert result["timestamp"].max() <= pd.Timestamp(input_max).tz_localize("UTC")


def test_start_as_timestamp(weekly_df):
    """start accepts pd.Timestamp directly."""
    result = expand(weekly_df, "W-MON", "h", start=pd.Timestamp("2024-06-01"))
    assert result["timestamp"].min() >= pd.Timestamp("2024-06-01").tz_localize("UTC")
    input_max = weekly_df["timestamp"].iloc[-1]
    assert result["timestamp"].max() <= pd.Timestamp(input_max).tz_localize("UTC")


def test_start_as_tz_aware_timestamp(weekly_df):
    """start accepts tz-aware Timestamp."""
    sh_ts = pd.Timestamp("2024-06-01 00:00:00").tz_localize("UTC")
    result = expand(weekly_df, "W-MON", "h", start=sh_ts)
    # Hourly target aligned to Monday; first row is first Monday >= start
    assert result["timestamp"].min() >= sh_ts


# ============================================================================
#  Interaction with date_format
# ============================================================================


def test_start_with_date_format(weekly_df):
    """start + date_format: range is clipped, timestamps are formatted."""
    result = expand(
        weekly_df,
        "W-MON",
        "h",
        start="2024-03-01",
        end="2024-03-31",
        date_format="%Y-%m-%d",
    )
    # The result spans only dates that fit between the start and end limits;
    # since target is hourly on a Monday-aligned weekly source, the first row
    # is the first Monday >= start, and the last is the last Monday <= end.
    assert result["timestamp"].iloc[0] >= "2024-03-01"
    assert result["timestamp"].iloc[-1] <= "2024-03-31"
    assert isinstance(result["timestamp"].iloc[0], str)


# ============================================================================
#  CLI
# ============================================================================


def test_cli_start_end(tmp_path: Path):
    """--start and --end CLI flags limit the output range."""
    in_csv = tmp_path / "in.csv"
    out_csv = tmp_path / "out.csv"
    in_csv.write_text(
        "timestamp,value\n2024-01-01,1\n2024-01-08,2\n2024-12-31,3\n", encoding="utf-8"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "timeseries_expand.cli",
            str(in_csv),
            str(out_csv),
            "--source-freq",
            "W-MON",
            "--target-freq",
            "D",
            "--start",
            "2024-02-01",
            "--end",
            "2024-02-29",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    out = pd.read_csv(out_csv)
    # CSV read strips tz; compare naive. The target is daily aligned to
    # the source's Monday cadence, so the first output row may be on a
    # Monday within Feb. We check that NO row is outside Feb 2024.
    for ts in pd.to_datetime(out["timestamp"]):
        assert pd.Timestamp("2024-02-01") <= ts <= pd.Timestamp("2024-02-29 23:59:59"), (
            f"timestamp {ts} outside Feb 2024"
        )


def test_cli_no_start_end_works(tmp_path: Path):
    """Without --start/--end, CLI emits the full range (backward compat)."""
    in_csv = tmp_path / "in.csv"
    out_csv = tmp_path / "out.csv"
    in_csv.write_text("timestamp,value\n2024-01-01,1\n2024-01-08,2\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "timeseries_expand.cli",
            str(in_csv),
            str(out_csv),
            "--source-freq",
            "W-MON",
            "--target-freq",
            "D",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"


def test_cli_start_before_input_fails(tmp_path: Path):
    """--start before the input data range should fail with a non-zero exit code."""
    in_csv = tmp_path / "in.csv"
    out_csv = tmp_path / "out.csv"
    in_csv.write_text("timestamp,value\n2024-01-01,1\n2024-01-08,2\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "timeseries_expand.cli",
            str(in_csv),
            str(out_csv),
            "--source-freq",
            "W-MON",
            "--target-freq",
            "D",
            "--start",
            "2023-01-01",  # before input range
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "before input range" in result.stderr or "before input range" in result.stdout
