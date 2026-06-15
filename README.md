# timeseries-expand

[![CI](https://github.com/Lance-Chen/timeseries-expand/actions/workflows/ci.yml/badge.svg)](https://github.com/Lance-Chen/timeseries-expand/actions)
[![PyPI](https://img.shields.io/pypi/v/timeseries-expand)](https://pypi.org/project/timeseries-expand/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

[English](#english) | [中文](#中文)

---

<a id="english"></a>

## English

**timeseries-expand** expands low-frequency time series into high-frequency series with **publication-aware forward fill** - every published value carries forward until the next publication, rather than being interpolated or back-filled.

Built for real-world data: weekly releases shifted by holidays, monthly indicators with occasional gaps, annual statistics that need daily granularity for downstream models.

### Why?

Most off-the-shelf resamplers assume strict periodicity. Real publishing schedules aren't like that:

- A weekly coal price index published on Monday - except when Monday is a public holiday, when it's pushed to Tuesday or Wednesday.
- A monthly indicator with the occasional skipped release.
- An annual figure that downstream code needs at hourly granularity.

`timeseries-expand` handles these cases explicitly and flags gaps so you can audit them later.

### Supported frequency ladder

Any source frequency can be expanded to any higher (finer) target frequency.

| Source / Target | Yearly | Quarterly | Monthly | Semi-Month | Weekly | Daily | Hourly |
|---|---|---|---|---|---|---|---|
| Yearly      | - | Y | Y | Y | Y | Y | Y |
| Quarterly   | - | - | Y | Y | Y | Y | Y |
| Monthly     | - | - | - | Y | Y | Y | Y |
| Semi-Month  | - | - | - | - | Y | Y | Y |
| Weekly      | - | - | - | - | - | Y | Y |
| Daily       | - | - | - | - | - | - | Y |
| Hourly      | - | - | - | - | - | - | - |

21 supported combinations.

### Install

```bash
pip install timeseries-expand
```

### Quick start

```python
import pandas as pd
from timeseries_expand import expand

# Weekly coal price index, published roughly every Monday
df = pd.DataFrame({
    "timestamp": pd.to_datetime([
        "2024-01-08", "2024-01-15", "2024-01-22",
        "2024-01-29", "2024-02-12",
    ]),
    "value": [101.5, 102.3, 103.1, 102.8, 104.2],
})

result = expand(df, source_freq="W-MON", target_freq="h")
print(result.head())
```

### Features

- **Publication-aware forward fill** - semantics `[T, T_next)` (carries forward until the next release)
- **Gap detection** - flags intervals exceeding 1.5x expected cadence with `gap_flag` column
- **DST-safe** - internal UTC, configurable display timezone
- **21 frequency combinations** - expand yearly/quarterly/monthly/weekly/daily data
- **173 tests** - pytest + Hypothesis property-based tests
- **3 call patterns** - functional API, class-based API, CLI



### Custom output date format

Pass `date_format` to format output timestamps as strings using any
[pandas strftime pattern](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes):

```python
# Functional API
result = expand(df, "W-MON", "h", date_format="%Y-%m-%d %H:%M")
# Result: "2024-01-01 00:00"

result = expand(df, "ME", "D", date_format="%Y-%m")
# Result: "2024-01" (year-month only)

result = expand(df, "W-MON", "D", date_format="%Y W%W")
# Result: "2024 W01" (ISO week)
```

CLI:

```bash
ts-expand in.csv out.csv --source-freq W-MON --target-freq h \
    --date-format "%Y-%m-%d"
```

**Common placeholders** (pandas supports a subset of strftime):
| code | meaning | example |
|------|---------|---------|
| `%Y` | 4-digit year | 2024 |
| `%m` | month (01-12) | 01 |
| `%d` | day of month (01-31) | 15 |
| `%H:%M` | hour:minute | 09:30 |
| `%a` | weekday abbr | Mon |
| `%b` | month abbr | Jan |
| `%j` | day of year (001-366) | 035 |
| `%W` | ISO week number (00-53) | 05 |
| `%z` | UTC offset | +0800 |

Omit `date_format` (default `None`) to keep output as `Timestamp` objects.


### Custom output time range

Clip the output to a subset of the input range with `start` / `end`:

```python
# Functional API
result = expand(df, "W-MON", "h", start="2024-03-01", end="2024-06-30")
# Output: 2024-03-01 to 2024-06-30 (clipped, no extrapolation)

result = expand(df, "W-MON", "h", start="2024-12-01")
# Only start: goes from 2024-12-01 to the input's last date
```

CLI:

```bash
ts-expand in.csv out.csv --source-freq W-MON --target-freq h \
    --start 2024-03-01 --end 2024-06-30
```

**Rules**:
- `start` / `end` must lie **within** the input data range; otherwise `ValueError`.
- `start > end` raises `ValueError` at config construction.
- Accepts ISO date strings, `pd.Timestamp`, or `datetime.date`. Naive values are assumed UTC.
- Combine with `date_format` for formatted output: `expand(df, "W-MON", "h", start="...", date_format="%Y-%m-%d")`.




### CLI

```bash
ts-expand input.csv output.csv --source-freq W-MON --target-freq h
ts-expand --version
```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

### License

MIT - see [LICENSE](LICENSE).

---

<a id="中文"></a>

## 中文

**timeseries-expand** 用"按发布时点的前向填充"语义，将低频时间序列扩充到高频 - 每个发布值沿用至下一次发布。

为真实场景设计：被节假日推迟的周度发布、偶尔缺失的月度指标、需要小时级粒度的年度统计数据。

### 支持的频率阶梯

任意源频率可扩充到任意更高的目标频率。共支持 21 种组合。

| 源 / 目标 | 年度 | 季度 | 月度 | 半月 | 周度 | 日度 | 小时 |
|---|---|---|---|---|---|---|---|
| 年度      | - | Y | Y | Y | Y | Y | Y |
| 季度      | - | - | Y | Y | Y | Y | Y |
| 月度      | - | - | - | Y | Y | Y | Y |
| 半月      | - | - | - | - | Y | Y | Y |
| 周度      | - | - | - | - | - | Y | Y |
| 日度      | - | - | - | - | - | - | Y |
| 小时      | - | - | - | - | - | - | - |

### 安装

```bash
pip install timeseries-expand
```

### 快速上手

```python
import pandas as pd
from timeseries_expand import expand

df = pd.DataFrame({
    "timestamp": pd.to_datetime([
        "2024-01-08", "2024-01-15", "2024-01-22",
        "2024-01-29", "2024-02-12",
    ]),
    "value": [101.5, 102.3, 103.1, 102.8, 104.2],
})

result = expand(df, source_freq="W-MON", target_freq="h")
print(result.head())
```

### 核心特性

- **按发布时点的前向填充** - 语义 `[T, T_next)`，沿用至下一次发布
- **间隙检测** - 默认 1.5 倍期望周期以上的间隔自动标记 `gap_flag`
- **DST 安全** - 内部 UTC，可配置显示时区
- **21 种频率组合** - 年级/季度/月度/半月/周度/日度数据任意扩充
- **173 个测试** - pytest + Hypothesis 属性测试
- **3 种调用方式** - 函数式 API、类 API、CLI



### 自定义输出时间范围

使用 `start` / `end` 把输出裁剪到输入的子区间：

```python
result = expand(df, "W-MON", "h", start="2024-03-01", end="2024-06-30")
# 输出：2024-03-01 到 2024-06-30（裁剪，不外推）

result = expand(df, "W-MON", "h", start="2024-12-01")
# 只给 start：从 2024-12-01 到输入的最后一个日期
```

CLI：

```bash
ts-expand in.csv out.csv --source-freq W-MON --target-freq h \
    --start 2024-03-01 --end 2024-06-30
```

**规则**：
- `start` / `end` 必须落在**输入数据范围内**，否则抛 `ValueError`。
- `start > end` 在配置构造时就抛 `ValueError`。
- 接受 ISO 日期字符串、`pd.Timestamp` 或 `datetime.date`，naive 值假定为 UTC。
- 可与 `date_format` 组合：`expand(df, "W-MON", "h", start="...", date_format="%Y-%m-%d")`。

### 命令行

```bash
ts-expand input.csv output.csv --source-freq W-MON --target-freq h
ts-expand --version
```

### 文档

GitHub: https://github.com/Lance-Chen/timeseries-expand  
PyPI: https://pypi.org/project/timeseries-expand/