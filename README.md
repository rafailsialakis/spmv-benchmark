# Sparse Matrix-Vector Multiplication Benchmark

This repository benchmarks Sparse Matrix-Vector Multiplication (SpMV) on
SuiteSparse matrices. It focuses on how matrix reordering affects runtime,
memory behavior, load balance, and the cost/benefit trade-off of preprocessing.

The benchmark core is written in C. Python is used for reading CSV outputs and
generating plots/tables.

## What Is Evaluated

Reordering methods:

- Reverse Cuthill-McKee (RCM)
- Approximate Minimum Degree (AMD)
- Nested Dissection (ND)

Measurement methods:

- Repeated `A * x` (RAx)
- Input/output vector swapping (IOs)
- Cold-cache style measurement

Additional measurements:

- Reordering time
- Matrix structural metrics
- Cache miss counters through PAPI
- TLB miss counters through PAPI
- x86 vs ARM comparisons when both result sets are available

## Repository Layout

```text
.
├── config/                 # Matrix source manifest
├── docs/                   # MkDocs documentation
├── figures/                # Generated plots and LaTeX tables
├── include/                # C headers
├── matrices/               # Downloaded SuiteSparse .mtx files, ignored by git
├── results/                # Generated benchmark CSVs, ignored by git
├── scripts/                # Download/run/analysis entry points
├── src/                    # C benchmark implementation
├── utils/                  # Python analysis modules
└── Makefile
```

Important generated paths:

```text
bin/
matrices/
results/x86_results/
results/arm_results/
figures/barcharts/
figures/overview/
figures/distributions/
figures/thesis/
figures/sparsity/
figures/tables/
```

## Dependencies

### C Benchmark

The Makefile expects:

- GCC
- OpenMP
- CXSparse / SuiteSparse
- Scotch METIS compatibility headers and libraries
- PAPI
- standard math library

The current link flags are:

```make
-lcxsparse -lscotchmetisv5 -lscotcherr -lm -lpapi
```

The Makefile also includes Scotch headers from:

```make
-I/usr/include/scotch
```

Adjust `CFLAGS`/`LDFLAGS` in `Makefile` if your system installs these libraries
elsewhere.

### Python Analysis

The analysis scripts use:

- pandas
- matplotlib
- seaborn
- scipy

### Documentation

The docs use MkDocs Material:

```bash
pip install -r docs/requirements.txt
```

## 1. Download Matrices

Matrix downloads are configured in:

```text
config/matrix_sources.tsv
```

The manifest is tab-separated:

```text
category    output_file.mtx    archive_url    [tar_member]
```

Download all configured matrices:

```bash
scripts/download_matrices.sh
```

This creates:

```text
matrices/<category>/<matrix>.mtx
```

Example:

```text
matrices/Structural/inline_1.mtx
matrices/Semiconductor/nv2.mtx
```

Useful options:

```bash
# Use a custom matrix root
MATRIX_ROOT=/tmp/spmv-matrices scripts/download_matrices.sh

# Overwrite existing matrices
FORCE=1 scripts/download_matrices.sh

# Use a custom manifest
scripts/download_matrices.sh path/to/matrix_sources.tsv
```

The downloader extracts only the wanted `.mtx` file from each SuiteSparse
archive and validates that it looks like a Matrix Market file.

## 2. Build

Build all benchmark binaries:

```bash
make all
```

This produces:

```text
bin/spmv-benchmark
bin/spmv-benchmark-perm
bin/spmv-benchmark-cache
bin/spmv-benchmark-tlb
```

It also creates:

```text
results/x86_results/
results/arm_results/
```

## 3. Run One Matrix

Pass paths relative to `matrices/`, not full filesystem paths.

```bash
make run MTX=Structural/inline_1.mtx
```

Other single-matrix targets:

```bash
make run-cache MTX=Structural/inline_1.mtx
make run-tlb MTX=Structural/inline_1.mtx
make run-perm MTX=Structural/inline_1.mtx
```

## 4. Run All Matrices

Run main timing benchmarks and structural metrics:

```bash
make run-all
```

Run TLB counters:

```bash
make run-all-tlb
```

Run cache counters:

```bash
make run-all-cache
```

Run the full local pipeline:

```bash
scripts/run_all.sh
```

That script runs:

```bash
make run-all
make run-all-tlb
make run-all-cache
make plot
```

## 5. Result CSVs

The benchmark writes to a platform-specific directory selected at compile time:

```text
results/x86_results/
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

These files are generated data and are ignored by git.

## 6. Generate Plots and Tables

Run:

```bash
make plot
```

Equivalent direct command:

```bash
python3 -m scripts.analysis
```

Do not run `python3 scripts/analysis.py`; the module form keeps imports rooted
at the project package layout.

The analysis tolerates missing platform data. For example, if ARM CSVs are not
available yet, x86 plots/tables are generated and ARM-specific outputs are
skipped with warnings.

Generated outputs:

```text
figures/barcharts/
figures/overview/
figures/distributions/
figures/thesis/
figures/sparsity/
figures/tables/
```

Increase logging verbosity with:

```bash
LOG_LEVEL=DEBUG python3 -m scripts.analysis
```

## 7. Clean

Remove binaries and result CSVs:

```bash
make clean
```

This does not remove downloaded matrices or generated figures.

## Documentation

Serve the documentation locally:

```bash
mkdocs serve -f docs/mkdocs.yml
```

Build the static docs site:

```bash
mkdocs build -f docs/mkdocs.yml
```

## Notes

- `matrices/` is ignored by git because SuiteSparse inputs are downloaded.
- `results/x86_results/` and `results/arm_results/` are ignored because they are
  generated benchmark data.
- Cache and TLB measurements depend on PAPI event availability and hardware
  counter permissions.
- Cross-platform plots require both x86 and ARM CSVs. They are skipped until
  both datasets exist.
