# SpMV Benchmark

This project benchmarks Sparse Matrix-Vector Multiplication (SpMV) on SuiteSparse
matrices. It evaluates how matrix reorderings affect execution time, cache/TLB
behavior, load balance, and structural matrix metrics.

The benchmark core is written in C. Python is used only for reading result CSVs
and generating figures/tables.

## What It Measures

- SpMV performance with different measurement methodologies:
  - repeated `A * x`
  - input/output vector swapping
  - cold-cache style measurement
- Reordering impact for:
  - Reverse Cuthill-McKee
  - Approximate Minimum Degree
  - Nested Dissection
- Reordering cost.
- Matrix structure metrics.
- Cache and TLB behavior through PAPI counters.

## Main Workflow

Run commands from the project root:

```bash
scripts/download_matrices.sh
make all
make run-all
make run-all-tlb
make run-all-cache
make plot
```

The shortcut script runs the benchmark and plotting pipeline:

```bash
scripts/run_all.sh
```

## Output Locations

- Benchmark CSVs: `results/x86_results/` or `results/arm_results/`
- Figures:
  - `figures/heatmaps/`
  - `figures/barcharts/`
  - `figures/faceted/`
  - `figures/sparsity/`
- LaTeX tables: `figures/tables/`

## Documentation

Serve these docs locally with:

```bash
mkdocs serve -f docs/mkdocs.yml
```

Build the static docs site with:

```bash
mkdocs build -f docs/mkdocs.yml
```
