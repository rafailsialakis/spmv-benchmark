# Analysis Outputs

Python analysis reads benchmark CSV files and writes figures/tables.

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

!!! warning "Mixed platform data"
    Some plots compare x86 and ARM directly. Those plots require both
    `results/x86_results/` and `results/arm_results/` to be populated with
    compatible matrix sets. If one platform is missing a matrix, the merge step
    may drop it from cross-platform comparisons.

!!! note "Missing platform data"
    The analysis pipeline tolerates missing CSVs. If ARM results are not present
    yet, x86 plots and tables are still generated while ARM-specific and
    cross-platform outputs are skipped with warnings.

## Plot Modules

Plotting code lives under:

```text
utils/plotting/
```

Module responsibilities:

`overview.py`
: Scalable ECDF and counter summary plots that remain readable for large matrix
sets.

`barcharts.py`
: Win/loss summaries and ARM-vs-x86 comparison.

`distributions.py`
: Runtime, counter, break-even, and structural metric histograms.

`thesis.py`
: Ranked and grouped thesis figures.

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
        ├── utils/plotting/overview.py
        ├── utils/plotting/barcharts.py
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
figures/barcharts/
figures/overview/
figures/distributions/
figures/thesis/
figures/sparsity/
figures/tables/
```

Examples:

```text
figures/barcharts/win_loss_ARM.pdf
figures/overview/speedup_ecdf_x86.pdf
figures/distributions/cache_reduction_histogram_x86.pdf
figures/thesis/best_speedup_ranked_x86.pdf
figures/tables/scaling_table_ARM.tex
```

## Expected CSV Inputs

| File | Producer | Main use |
| --- | --- | --- |
| `metrics.csv` | `make run-all` | Matrix characteristics and structural compression plots |
| `reorder_times.csv` | `make run-all` | Break-even tables |
| `rax.csv` | `make run-all` | Speedup overviews, scaling, win/loss summaries |
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

sparse_plot("matrices/Semiconductor/nv2.mtx")
```

The output goes to:

```text
figures/sparsity/
```
