"""Test the public API surface (functional + class-based)."""

from __future__ import annotations

import inspect

import pandas as pd
import pytest

import timeseries_expand
from timeseries_expand import ExpandConfig, FrequencyExpander, Frequency, expand


def test_public_api_exports():
    """Verify the public API exports the documented names."""
    assert hasattr(timeseries_expand, "expand")
    assert hasattr(timeseries_expand, "ExpandConfig")
    assert hasattr(timeseries_expand, "FrequencyExpander")
    assert hasattr(timeseries_expand, "Frequency")
    assert "expand" in timeseries_expand.__all__


def test_functional_api_basic():
    """expand() works with string frequency aliases."""
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
        "value": [100.0, 101.0, 102.0],
    })
    result = expand(df, "W-MON", "h")
    assert "timestamp" in result.columns
    assert "value" in result.columns
    assert "gap_flag" in result.columns
    assert len(result) > 0


def test_functional_api_matches_class_api():
    """The functional API must produce identical output to the class API."""
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
        "value": [100.0, 101.0, 102.0],
    })

    result_func = expand(df, "W-MON", "h")

    cfg = ExpandConfig(source_freq=Frequency.WEEKLY, target_freq=Frequency.HOURLY)
    result_class = FrequencyExpander().expand(df, cfg)

    assert len(result_func) == len(result_class)
    assert result_func["timestamp"].tolist() == result_class["timestamp"].tolist()
    assert result_func["value"].tolist() == result_class["value"].tolist()


def test_functional_api_passes_kwargs():
    """timezone, gap_threshold_multiplier, time_col, value_col all work."""
    df = pd.DataFrame({
        "ts": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
        "price": [100.0, 101.0, 102.0],
    })
    result = expand(
        df, "W-MON", "h",
        timezone="Asia/Shanghai",
        gap_threshold_multiplier=2.0,
        time_col="ts",
        value_col="price",
    )
    assert "price" in result.columns
    assert "ts" in result.columns
    assert str(result["ts"].iloc[0].tz) == "Asia/Shanghai"


def test_functional_api_docstring():
    """expand() must have a docstring with an Example section."""
    assert expand.__doc__ is not None
    assert "Example" in expand.__doc__
    assert "Args" in expand.__doc__


def test_functional_api_signature():
    """expand() signature should match the documented public API."""
    sig = inspect.signature(expand)
    params = sig.parameters
    assert "df" in params
    assert "source_freq" in params
    assert "target_freq" in params
    assert "timezone" in params
    assert "gap_threshold_multiplier" in params
    assert "time_col" in params
    assert "value_col" in params
