# Analysis Pipeline

Python analysis reads benchmark CSV files and writes reproducible figures and
tables for the benchmark report.

Run:

```bash
make plot
```

or directly:

```bash
python3 -m scripts.analysis
```

The module form is intentional: it keeps imports rooted at the project package
layout without modifying `sys.path` inside the script.

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

!!! note "Missing platform data"
    The analysis pipeline tolerates missing CSVs. If ARM results are not present
    yet, x86 plots and tables are still generated while ARM-specific outputs are
    skipped with warnings.

## Plot Modules

Plotting code lives under:

```text
utils/plotting/
```

Module responsibilities:

`distributions.py`
: Speedup and structural compression histogram generation.

`thesis.py`
: Curated benchmark figures used by the report narrative.

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
        ├── utils/plotting/distributions.py
        ├── utils/plotting/thesis.py
        └── utils/plotting/tables.py
        │
        ▼
figures/<type>/
```

## Figure Directories

Figures are grouped by output type:

```text
figures/thesis/
figures/sparsity/
figures/tables/
```

Examples:

```text
figures/thesis/category_speedup_distribution_x86.pdf
figures/thesis/outcome_fraction_bars_x86.pdf
figures/distributions/speedup_histogram_x86.pdf
figures/thesis/preprocessing_breakeven_boxplot_x86.pdf
figures/thesis/best_reordering_agreement.pdf
figures/thesis/cache_miss_ratio_summary_x86.pdf
figures/thesis/methodology_fraction_scatter_x86.pdf
figures/distributions/structural_compression_histogram_x86.pdf
figures/tables/matrix_characteristics.tex
```

## Expected CSV Inputs

| File | Producer | Main use |
| --- | --- | --- |
| `metrics.csv` | `make run-all` | Matrix characteristics and structural compression plots |
| `reorder_times.csv` | `make run-all` | Preprocessing break-even plots |
| `rax.csv` | `make run-all` | Speedup distributions and outcome fractions |
| `ios.csv` | `make run-all` | Measurement methodology plots |
| `cold.csv` | `make run-all` | Measurement methodology plots |
| `cache.csv` | `make run-all-cache` | Cache miss plots |
| `tlb.csv` | `make run-all-tlb` | TLB miss plots |

## Sparsity Plots

Sparsity plotting is not part of the default `make plot` pipeline because it
requires permutation vectors in `validation/`.

To generate one manually, enable the commented hook in `scripts/analysis.py` or
call the function directly:

```python
from utils.plotting.sparsity import sparse_plot

sparse_plot("matrices/Semiconductor/nv2.mtx")
```

The output goes to:

```text
figures/sparsity/
```
