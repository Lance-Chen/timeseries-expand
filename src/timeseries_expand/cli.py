"""Command-line interface for timeseries-expand."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from timeseries_expand import ExpandConfig, FrequencyExpander, __version__
from timeseries_expand.frequencies import Frequency


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ts-expand",
        description="Expand a low-frequency time series to a higher frequency.",
    )
    parser.add_argument("--version", action="version", version=f"ts-expand {__version__}")
    parser.add_argument(
        "input", nargs="?", type=Path, help="Input CSV file with [timestamp,value] columns"
    )
    parser.add_argument("output", nargs="?", type=Path, help="Output CSV path")
    parser.add_argument(
        "--source-freq",
        type=Frequency.parse,
        required=False,
        help=f"Source frequency. One of: {[f.value for f in Frequency]}",
    )
    parser.add_argument(
        "--target-freq",
        type=Frequency.parse,
        required=False,
        help="Target frequency.",
    )
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument(
        "--start",
        default=None,
        help="Optional lower bound for output timestamps (e.g. '2024-03-01'). "
        "Must lie within the input data range.",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Optional upper bound for output timestamps. Must lie within input.",
    )
    parser.add_argument(
        "--date-format",
        default=None,
        help="Optional strftime pattern for output timestamps (e.g. '%%Y-%%m-%%d %%H:%%M'). "
        "If omitted, timestamps are written as ISO 8601 strings by pandas.",
    )
    parser.add_argument("--time-col", default="timestamp", help="Timestamp column name")
    parser.add_argument("--value-col", default="value", help="Value column name")
    args = parser.parse_args()

    # --version is handled by argparse automatically
    if not args.input or not args.output:
        if len(sys.argv) <= 1:
            parser.print_help()
            return
        parser.error("input and output files are required")

    df = pd.read_csv(args.input)
    cfg = ExpandConfig(
        source_freq=args.source_freq,
        target_freq=args.target_freq,
        timezone=args.timezone,
        date_format=args.date_format,
        start=args.start,
        end=args.end,
    )
    result = FrequencyExpander().expand(df, cfg, time_col=args.time_col, value_col=args.value_col)
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} rows to {args.output}")


if __name__ == "__main__":
    main()
