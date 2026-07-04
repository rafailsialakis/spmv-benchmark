# Analysis Outputs

Python analysis reads benchmark CSV files and writes figures/tables.

Run:

```bash
make plot
```

or directly:

```bash
python3 scripts/analysis.py
```

## Data Loading

CSV reading and plotting configuration live in:

```text
utils/data/io.py
```

The reader expects:

```text
results/x86_results/
results/arm_results/
```

Both platform result directories must contain the CSVs needed by the analysis.

!!! warning "Mixed platform data"
    Some plots compare x86 and ARM directly. Those plots require both
    `results/x86_results/` and `results/arm_results/` to be populated with
    compatible matrix sets. If one platform is missing a matrix, the merge step
    may drop it from cross-platform comparisons.

## Plot Modules

Plotting code lives under:

```text
utils/plotting/
```

Module responsibilities:

`heatmaps.py`
: Speedup heatmaps.

`barcharts.py`
: Win/loss summaries and ARM-vs-x86 comparison.

`faceted.py`
: Cache and TLB faceted plots.

`sparsity.py`
: Matrix sparsity pattern plots.

`tables.py`
: LaTeX table generation.

`common.py`
: Shared figure saving helper.

## Pipeline Shape

```text
results/<platform>_results/*.csv
        │
        ▼
utils/data/io.py
        │
        ▼
scripts/analysis.py
        │
        ├── utils/plotting/heatmaps.py
        ├── utils/plotting/barcharts.py
        ├── utils/plotting/faceted.py
        └── utils/plotting/tables.py
        │
        ▼
figures/<type>/
```

## Figure Directories

Figures are grouped by output type:

```text
figures/heatmaps/
figures/barcharts/
figures/faceted/
figures/sparsity/
figures/tables/
```

Examples:

```text
figures/heatmaps/speedup_heatmap_x86.pdf
figures/barcharts/win_loss_ARM.pdf
figures/faceted/cache_miss_faceted_x86.pdf
figures/tables/scaling_table_ARM.tex
```

## Expected CSV Inputs

| File | Producer | Main use |
| --- | --- | --- |
| `metrics.csv` | `make run-all` | Matrix characteristics and normalized cache plots |
| `reorder_times.csv` | `make run-all` | Break-even tables |
| `rax.csv` | `make run-all` | Heatmaps, scaling, win/loss summaries |
| `ios.csv` | `make run-all` | Methodology comparison |
| `cold.csv` | `make run-all` | Methodology and ARM-vs-x86 comparison |
| `cache.csv` | `make run-all-cache` | Cache miss plots |
| `tlb.csv` | `make run-all-tlb` | TLB miss plots |

## Sparsity Plots

Sparsity plotting is not part of the default `make plot` pipeline because it
requires permutation vectors in `validation/`.

To generate one manually, enable the commented hook in `scripts/analysis.py` or
call the function directly:

```python
from utils.plotting.sparsity import sparse_plot

sparse_plot("matrices/Circuit/nv2.mtx")
```

The output goes to:

```text
figures/sparsity/
```
