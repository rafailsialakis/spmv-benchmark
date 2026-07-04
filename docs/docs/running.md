# Running Benchmarks

Run commands from the project root.

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
