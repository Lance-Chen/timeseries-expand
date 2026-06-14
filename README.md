# timeseries-expand

[![CI](https://github.com/Lance-Chen/timeseries-expand/actions/workflows/ci.yml/badge.svg)](https://github.com/Lance-Chen/timeseries-expand/actions)
[![PyPI](https://img.shields.io/pypi/v/timeseries-expand)](https://pypi.org/project/timeseries-expand/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)

[English](#english) | [中文](#中文)

---

<a id="english"></a>

## English

**timeseries-expand** expands low-frequency time series into high-frequency series with **publication-aware forward fill** — every published value carries forward until the next publication, rather than being interpolated or back-filled.

Built for real-world data: weekly releases shifted by holidays, monthly indicators with occasional gaps, annual statistics that need daily granularity for downstream models.

### Why?

Most off-the-shelf resamplers assume strict periodicity. Real publishing schedules aren't like that:

- A weekly coal price index published on Monday — except when Monday is a public holiday, when it's pushed to Tuesday or Wednesday.
- A monthly indicator with the occasional skipped release.
- An annual figure that downstream code needs at hourly granularity.

`timeseries-expand` handles these cases explicitly and flags gaps so you can audit them later.

### Supported frequency ladder

Any source frequency can be expanded to any higher (finer) target frequency.
The expansion rule is uniform: **every published value carries forward until
the next publication** (publication-aware forward fill, semantics `[T, T_next)`).

| Source ↓ / Target → | Yearly | Quarterly | Monthly | Semi-Month | Weekly | Daily | Hourly |
|---|---|---|---|---|---|---|---|
| Yearly      | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Quarterly   | – | – | ✓ | ✓ | ✓ | ✓ | ✓ |
| Monthly     | – | – | – | ✓ | ✓ | ✓ | ✓ |
| Semi-Month  | – | – | – | – | ✓ | ✓ | ✓ |
| Weekly      | – | – | – | – | – | ✓ | ✓ |
| Daily       | – | – | – | – | – | – | ✓ |
| Hourly      | – | – | – | – | – | – | – |

21 supported combinations. Adding new frequencies is a single edit to the
`Frequency` enum.

### Install

```bash
pip install timeseries-expand
```

With Polars backend (faster on large inputs):

```bash
pip install timeseries-expand[polars]
```

### Quick start

```python
import pandas as pd
from timeseries_expand import ExpandConfig, FrequencyExpander

# Weekly coal price index, published roughly every Monday
df = pd.DataFrame({
    "timestamp": pd.to_datetime([
        "2024-01-08", "2024-01-15", "2024-01-22",  # normal weeks
        "2024-01-29",                              # pushed by holiday
        "2024-02-12",                              # Spring Festival gap
    ]),
    "value":     [101.5, 102.3, 103.1, 102.8, 104.2],
})

cfg = ExpandConfig(source_freq="W-MON", target_freq="h")
result = FrequencyExpander().expand(df, cfg)

print(result.head())
#                  timestamp  value  gap_flag
# 0  2024-01-08 00:00:00+00:00  101.5     False
# 1  2024-01-08 01:00:00+00:00  101.5     False
# ...
```

### Examples

Run any of these from the project root:

```bash
# Weekly coal price -> hourly (uses examples/coal_price_weekly.csv)
ts-expand examples/coal_price_weekly.csv /tmp/coal_hourly.csv \
    --source-freq W-MON --target-freq h --timezone UTC

# Annual index -> daily
ts-expand examples/annual_index.csv /tmp/annual_daily.csv \
    --source-freq YE --target-freq D

# Monthly index -> weekly in Asia/Shanghai timezone
ts-expand examples/monthly_index.csv /tmp/monthly_weekly.csv \
    --source-freq ME --target-freq W-MON --timezone Asia/Shanghai

# Semi-monthly -> hourly
ts-expand examples/semi_monthly.csv /tmp/semi_monthly_hourly.csv \
    --source-freq SME --target-freq h
```

### Features

- **Publication-aware forward fill** — semantics `[T, T_next)` (carries forward to, but not including, the next release).
- **Gap detection** — flags intervals exceeding 1.5× expected cadence; configurable via `gap_threshold_multiplier`.
- **Timezone-safe** — internal UTC; DST-safe across all transitions.
- **Irregular schedule-tolerant** — handles 6/8/9-day "weekly" gaps without crashing.
- **Property-tested** — Hypothesis suite guarantees published values are preserved exactly.

### Documentation

Full docs at <https://Lance-Chen.github.io/timeseries-expand/>.

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and feature requests welcome via [GitHub Issues](../../issues).

### License

MIT — see [LICENSE](LICENSE).

---

<a id="中文"></a>

## 中文

**timeseries-expand** 用「**按发布时点的前向填充**」语义，将低频时间序列扩充到高频——每个发布值沿用至下一次发布，而非插值或反向填充。

为真实场景设计：被节假日推迟的周度发布、偶尔缺失的月度指标、需要小时级粒度的年度统计数据。

### 为什么需要它？

现成的时间序列库都假设严格的周期性，但真实的发布日程并非如此：

- 煤价指数每周一发布——但如果周一是法定节假日，可能推迟到周二或周三。
- 月度指标偶尔会缺失某一期。
- 年度数据，下游模型需要日级甚至小时级粒度。

`timeseries-expand` 显式处理这些场景，并通过 `gap_flag` 标记异常，便于后续审查。

### 支持的频率阶梯

任意源频率可扩充到任意更高的目标频率。
扩充规则统一：**每个发布值沿用至下一次发布**（按发布时点的前向填充，语义 `[T, T_next)`）。

| 源 ↓ / 目标 → | 年度 | 季度 | 月度 | 半月 | 周度 | 日度 | 小时 |
|---|---|---|---|---|---|---|---|
| 年度      | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 季度      | – | – | ✓ | ✓ | ✓ | ✓ | ✓ |
| 月度      | – | – | – | ✓ | ✓ | ✓ | ✓ |
| 半月      | – | – | – | – | ✓ | ✓ | ✓ |
| 周度      | – | – | – | – | – | ✓ | ✓ |
| 日度      | – | – | – | – | – | – | ✓ |
| 小时      | – | – | – | – | – | – | – |

共支持 21 种组合。增加新频率只需修改 `Frequency` 枚举一行。

### 安装

```bash
pip install timeseries-expand
```

启用 Polars 后端（大数据量更快）：

```bash
pip install timeseries-expand[polars]
```

### 快速上手

```python
import pandas as pd
from timeseries_expand import ExpandConfig, FrequencyExpander

# 煤价指数，每周大致周一发布
df = pd.DataFrame({
    "timestamp": pd.to_datetime([
        "2024-01-08", "2024-01-15", "2024-01-22",  # 正常周
        "2024-01-29",                              # 节假日推迟
        "2024-02-12",                              # 春节假期空档
    ]),
    "val