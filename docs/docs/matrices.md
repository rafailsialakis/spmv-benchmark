# Matrices

Matrices come from the SuiteSparse Matrix Collection and are stored locally in
Matrix Market format.

## Manifest

The download manifest is:

```text
config/matrix_sources.tsv
```

It is tab-separated and has this format:

```text
category    output_file.mtx    archive_url    [tar_member]
```

Fields:

- `category`: directory under `matrices/`, for example `Structural` or `Circuit`.
- `output_file.mtx`: final Matrix Market filename.
- `archive_url`: SuiteSparse `.tar.gz` URL.
- `tar_member`: optional exact `.mtx` member to extract from the archive.

Blank lines and `#` comments are ignored.

The manifest groups matrices by benchmark domain rather than by SuiteSparse
collection group. Current categories are `Structural`, `Geomechanics`, `PDE`,
`CFD`, `Optimization`, `Circuit`, `Semiconductor`, and `ModelReduction`. The
active set is chosen to keep structurally symmetric sparsity patterns for
reordering experiments.

## Download

Run from the project root:

```bash
scripts/download_matrices.sh
```

By default the script reads:

```text
config/matrix_sources.tsv
```

and writes matrices into:

```text
matrices/
```

The resulting structure is:

```text
matrices/Structural/inline_1.mtx
matrices/PDE/thermal2.mtx
matrices/Semiconductor/nv2.mtx
...
```

## Custom Manifest

You can pass a custom manifest:

```bash
scripts/download_matrices.sh path/to/matrix_sources.tsv
```

## Environment Variables

`MATRIX_ROOT`
: Override where matrices are written.

```bash
MATRIX_ROOT=/tmp/spmv-matrices scripts/download_matrices.sh
```

`FORCE`
: Overwrite existing `.mtx` files.

```bash
FORCE=1 scripts/download_matrices.sh
```

## Extraction Behavior

The downloader:

1. Creates `matrices/<category>/`.
2. Downloads the `.tar.gz` archive.
3. Extracts only the requested `.mtx` file.
4. Validates that the extracted file starts with `%%MatrixMarket`.
5. Skips existing matrices unless `FORCE=1` is set.

This keeps archive contents out of the benchmark input tree and leaves only the
matrix files that `make run-all` should discover.
