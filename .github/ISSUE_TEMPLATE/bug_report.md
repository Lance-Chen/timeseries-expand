---
name: Bug report
about: Report incorrect behavior or unexpected output
title: "[Bug] "
labels: bug
assignees: ""
---

## Description
A clear description of what the bug is.

## Reproducible example
```python
import pandas as pd
from timeseries_expand import FrequencyExpander

# Minimal code that triggers the bug
df = pd.DataFrame(...)
result = FrequencyExpander().expand(df, ...)
```

## Expected behavior
What you expected to happen.

## Actual behavior
What actually happened.

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- pandas version: [e.g., 2.2.2]
- timeseries-expand version: [e.g., 0.1.0]

## Additional context
Any other relevant info (logs, screenshots, etc.).