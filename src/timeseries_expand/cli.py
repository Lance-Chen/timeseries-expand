"""Command-line interface for timeseries-expand."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from timeseries_expand import ExpandConfig, FrequencyExpander
from timeseries_expand.frequencies import Frequency


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ts-expand",
        description="Expand a low-frequency time series to a higher frequency.",
    )
    parser.add_argument("input", type=Path, help="Input CSV file with [timestamp,value] columns")
    parser.add_argument("output", type=Path, help="Output CSV path")
    parser.add_argument(
        "--source-freq",
        type=Frequency.parse,
        required=True,
        help=f"Source frequency. One of: {[f.value for f in Frequency]}",
    )
    parser.add_argument(
        "--target-freq",
        type=Frequency.parse,
        required=True,
        help="Target frequency.",
    )
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument(
        "--time-col", default="timestamp", help="Timestamp column name"
    )
    parser.add_argument(
        "--value-col", default="value", help="Value column name"
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    cfg = ExpandConfig(
        source_freq=args.source_freq,
        target_freq=args.target_freq,
        timezone=args.timezone,
    )
    result = FrequencyExpander().expand(
        df, cfg, time_col=args.time_col, value_col=args.value_col
    )
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} rows to {args.output}")


if __name__ == "__main__":
    main()