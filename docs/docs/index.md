# Benchmark Documentation

Operational documentation for the Sparse Matrix-Vector Multiplication (SpMV)
benchmark. The benchmark evaluates how matrix reordering changes runtime,
memory-system behavior, and preprocessing trade-offs across SuiteSparse matrix
families.

The execution core is implemented in C. Python is used for CSV ingestion,
analysis, figure generation, and table output.

<div class="enterprise-summary" markdown>

| Area | Scope |
| --- | --- |
| Kernel | CSR SpMV with original and reordered matrices |
| Reorderings | RCM, AMD, nested dissection, and graph partitioning |
| Measurements | Runtime, GFLOP/s, preprocessing cost, cache misses, TLB misses |
| Platforms | x86 and ARM result schemas |
| Outputs | CSV results, benchmark figures, and LaTeX tables |

</div>

## Goals

The benchmark is built around a practical question: when does paying the cost of
matrix reordering improve SpMV enough to matter?

It records:

- SpMV runtime and GFLOP/s across measurement methodologies.
- Reordering cost for RCM, AMD, ND, and GP.
- Structural matrix metrics such as bandwidth, density, and load imbalance.
- Cache and TLB counter behavior through PAPI.
- Cross-platform behavior on x86 and ARM systems.

!!! note "Why this is memory-focused"
    SpMV usually performs little arithmetic per byte moved. Performance is often
    limited by sparse access patterns, cache reuse, TLB behavior, and memory
    bandwidth rather than floating-point throughput.

## Standard Workflow

Run commands from the project root:

```bash
scripts/download_matrices.sh
make all
make run-all
make run-all-tlb
make run-all-cache
make plot
```

`make plot` runs the analysis as a module:

```bash
python3 -m scripts.analysis
```

The shortcut script runs the benchmark and plotting pipeline:

```bash
scripts/run_all.sh
```

## Artifact Map

| Artifact | Location |
| --- | --- |
| Download manifest | `config/matrix_sources.tsv` |
| Matrix files | `matrices/<category>/<matrix>.mtx` |
| x86 CSVs | `results/x86_results/` |
| ARM CSVs | `results/arm_results/` |
| Benchmark figures | `figures/thesis/` |
| Sparsity plots | `figures/sparsity/` |
| LaTeX tables | `figures/tables/` |

## Local Documentation

Serve these docs locally with:

```bash
cd docs
zensical serve
```

Build the static docs site with:

```bash
cd docs
zensical build
```

From the project root, use:

```bash
make docs
```

The documentation uses Zensical. Install the docs dependency with:

```bash
pip install -r docs/requirements.txt
```
