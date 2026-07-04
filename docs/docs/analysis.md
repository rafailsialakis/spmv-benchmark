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
