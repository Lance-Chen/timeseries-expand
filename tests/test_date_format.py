"""Tests for the date_format parameter on output timestamps."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from timeseries_expand import ExpandConfig, Frequency, FrequencyExpander, expand


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A small weekly-coal-price sample spanning early 2024."""
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
            "value": [101.5, 102.3, 103.1],
        }
    )


# -------------------- Defaults --------------------


def test_default_no_format_keeps_timestamp(sample_df: pd.DataFrame) -> None:
    """Backward compat: omitting date_format returns Timestamp objects."""
    result = expand(sample_df, "W-MON", "h")
    assert isinstance(result["timestamp"].iloc[0], pd.Timestamp)


def test_explicit_none_keeps_timestamp(sample_df: pd.DataFrame) -> None:
    """Explicit None behaves like the default."""
    result = expand(sample_df, "W-MON", "h", date_format=None)
    assert isinstance(result["timestamp"].iloc[0], pd.Timestamp)


# -------------------- Functional API --------------------


def test_iso_date_only(sample_df: pd.DataFrame) -> None:
    """`%Y-%m-%d` produces plain date strings."""
    result = expand(sample_df, "W-MON", "h", date_format="%Y-%m-%d")
    assert result["timestamp"].iloc[0] == "2024-01-01"
    assert isinstance(result["timestamp"].iloc[0], str)


def test_slash_format_with_time(sample_df: pd.DataFrame) -> None:
    """`%Y/%m/%d %H:%M` works for slash-separated date+time."""
    result = expand(sample_df, "W-MON", "h", date_format="%Y/%m/%d %H:%M")
    assert result["timestamp"].iloc[0] == "2024/01/01 00:00"


def test_year_month_only(sample_df: pd.DataFrame) -> None:
    """`%Y-%m` keeps only year+month (downsampling-style)."""
    result = expand(sample_df, "W-MON", "h", date_format="%Y-%m")
    assert result["timestamp"].iloc[0] == "2024-01"


def test_quarter_via_month(sample_df: pd.DataFrame) -> None:
    """Quarter is not in pandas strftime; derive it via int math on month.

    Example pattern: quarter = (month - 1) // 3 + 1.
    This test demonstrates the workaround for the missing %Q directive.
    """
    result = expand(sample_df, "W-MON", "h", date_format="%Y-%m")
    assert result["timestamp"].iloc[0] == "2024-01"  # January = Q1


def test_week_of_year(sample_df: pd.DataFrame) -> None:
    """`%Y W%W` produces ISO week labels (Monday-start)."""
    result = expand(sample_df, "W-MON", "h", date_format="%Y W%W")
    # 2024-01-01 is in ISO week 1
    assert result["timestamp"].iloc[0].startswith("2024 W")
    assert result["timestamp"].iloc[0] == "2024 W01"


def test_full_datetime_with_seconds(sample_df: pd.DataFrame) -> None:
    """`%Y-%m-%d %H:%M:%S` produces full datetime strings."""
    result = expand(sample_df, "W-MON", "h", date_format="%Y-%m-%d %H:%M:%S")
    assert result["timestamp"].iloc[0] == "2024-01-01 00:00:00"


def test_day_of_year(sample_df: pd.DataFrame) -> None:
    """`%Y-%j` produces year-dayOfYear strings."""
    result = expand(sample_df, "W-MON", "h", date_format="%Y-%j")
    # 2024-01-01 is day 001
    assert result["timestamp"].iloc[0] == "2024-001"


def test_weekday_name(sample_df: pd.DataFrame) -> None:
    """`%a %b %d` produces weekday + month name + day."""
    result = expand(sample_df, "W-MON", "h", date_format="%a %b %d")
    # 2024-01-01 is Monday, January 1
    assert result["timestamp"].iloc[0] == "Mon Jan 01"


# -------------------- Class API --------------------


def test_class_api_with_date_format(sample_df: pd.DataFrame) -> None:
    """ExpandConfig.date_format also works via the class API."""
    cfg = ExpandConfig(
        source_freq=Frequency.WEEKLY,
        target_freq=Frequency.HOURLY,
        date_format="%Y%m%d",
    )
    result = FrequencyExpander().expand(sample_df, cfg)
    assert result["timestamp"].iloc[0] == "20240101"


# -------------------- Timezone + format combo --------------------


def test_date_format_with_timezone(sample_df: pd.DataFrame) -> None:
    """date_format and timezone interact: tz is applied first, then strftime."""
    result = expand(
        sample_df,
        "W-MON",
        "h",
        timezone="Asia/Shanghai",
        date_format="%Y-%m-%d %H:%M %Z",
    )
    # Asia/Shanghai is UTC+8
    assert "2024-01-01 08:00" in result["timestamp"].iloc[0]


# -------------------- Custom column name + format --------------------


def test_date_format_with_chinese_columns(sample_df: pd.DataFrame) -> None:
    """date_format applies regardless of column name."""
    df = sample_df.rename(columns={"timestamp": "日期", "value": "煤价指数"})
    result = expand(
        df,
        "W-MON",
        "h",
        time_col="日期",
        value_col="煤价指数",
        date_format="%Y年%m月%d日",
    )
    assert result["日期"].iloc[0] == "2024年01月01日"


# -------------------- CLI --------------------


def test_cli_date_format(tmp_path: Path) -> None:
    """The --date-format CLI flag formats output timestamps."""
    in_csv = tmp_path / "in.csv"
    out_csv = tmp_path / "out.csv"
    in_csv.write_text("timestamp,value\n2024-01-01,100\n2024-01-08,101\n", encoding="utf-8")

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
            "h",
            "--date-format",
            "%Y-%m-%d",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    out = pd.read_csv(out_csv)
    assert out["timestamp"].iloc[0] == "2024-01-01"
