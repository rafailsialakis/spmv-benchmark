# Running Benchmarks

Run commands from the project root.

!!! tip "Recommended order"
    Download matrices first, build all binaries, run the timing benchmarks,
    then run TLB/cache measurements. Cache and TLB runs use PAPI and are more
    sensitive to platform permissions and counter availability.

## Dependencies

The C benchmark expects:

- GCC
- OpenMP
- CXSparse / SuiteSparse headers and libraries
- Scotch METIS compatibility library
- PAPI
- math library

The Python analysis expects:

- pandas
- matplotlib
- seaborn
- scipy

The matrix downloader expects:

- `curl` or `wget`
- `tar`

## Build

```bash
make all
```

This builds:

```text
bin/spmv-benchmark
bin/spmv-benchmark-perm
bin/spmv-benchmark-cache
bin/spmv-benchmark-tlb
```

The build also ensures result directories exist:

```text
results/x86_results/
results/arm_results/
```

## Run One Matrix

Pass the matrix path relative to `matrices/`:

```bash
make run MTX=FEM/inline_1.mtx
```

Other single-matrix targets:

```bash
make run-cache MTX=FEM/inline_1.mtx
make run-tlb MTX=FEM/inline_1.mtx
make run-perm MTX=FEM/inline_1.mtx
```

The executable receives `FEM/inline_1.mtx`, not the full `matrices/...` path.
The C parser prepends the `matrices/` root internally.

## Run All Matrices

The all-matrix targets discover every `.mtx` under `matrices/`:

```bash
make run-all
make run-all-tlb
make run-all-cache
```

The full helper script runs all benchmark stages and then analysis:

```bash
scripts/run_all.sh
```

## Benchmark Stages

| Stage | Make target | Output |
| --- | --- | --- |
| Main timings and metrics | `make run-all` | `metrics.csv`, `reorder_times.csv`, `rax.csv`, `ios.csv`, `cold.csv` |
| TLB counters | `make run-all-tlb` | `tlb.csv` |
| Cache counters | `make run-all-cache` | `cache.csv` |
| Plots and tables | `make plot` | `figures/` |

## PAPI Notes

Cache and TLB runs use PAPI events. Availability depends on hardware, kernel
configuration, and permissions.

Common failure modes:

- PAPI cannot resolve the requested TLB events.
- The user does not have permission to access hardware counters.
- ARM and x86 expose different cache event sets.

The code already uses architecture-specific cache event columns: x86 writes L1,
L2, and L3 counters; ARM writes L1 and L2 counters.

## Result Files

On x86, output is written to:

```text
results/x86_results/
```

On ARM, output is written to:

```text
results/arm_results/
```

Expected CSV files:

```text
metrics.csv
reorder_times.csv
rax.csv
ios.csv
cold.csv
cache.csv
tlb.csv
```

## Clean

```bash
make clean
```

This removes compiled binaries and CSV result files from the platform result
directories. It does not remove downloaded matrices or generated figures.
