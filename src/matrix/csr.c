#include <stdio.h>
#include "matrix/coo.h"
#include "matrix/csr.h"

struct CSRMatrix* csr_from_coo(struct COOMatrix* coo_mtx){
    if (coo_mtx->metadata.rows <= 0 || coo_mtx->metadata.nnz < 0) {
        fprintf(stderr, "csr_from_coo: invalid dimensions\n");
        exit(EXIT_FAILURE);
    }
    struct CSRMatrix* csr_mtx = (struct CSRMatrix*) malloc(sizeof(struct CSRMatrix));
    csr_mtx->n = coo_mtx->metadata.rows;
    csr_mtx->nnz = coo_mtx->metadata.nnz;
    csr_mtx->row_ptr = (int*) calloc((size_t)csr_mtx->n + 1, sizeof(int));
    csr_mtx->col_idx = (int*) malloc(sizeof(int) * (size_t)csr_mtx->nnz);
    csr_mtx->values = (double*) malloc(sizeof(double) * (size_t)csr_mtx->nnz);
    for (int i = 0; i < csr_mtx->nnz; i++){
        csr_mtx->row_ptr[coo_mtx->row_idx[i] + 1]++;
    }
    for(int i = 1; i <= csr_mtx->n; i++){
        csr_mtx->row_ptr[i] += csr_mtx->row_ptr[i-1];
    }
    int* cursor = calloc((size_t)coo_mtx->metadata.rows, sizeof(int));
    for(int k = 0; k < csr_mtx->nnz; k++){
        int row = coo_mtx->row_idx[k];
        int pos = csr_mtx->row_ptr[row] + cursor[row]++;
        csr_mtx->col_idx[pos] = coo_mtx->col_idx[k];
        csr_mtx->values[pos] = coo_mtx->values[k];
    }
    free(cursor);
    return csr_mtx;
}

void csr_free(struct CSRMatrix* csr){
    free(csr->row_ptr);
    free(csr->col_idx);
    free(csr->values);
    free(csr);
}

long long csr_duplicate_entries(const struct CSRMatrix* csr) {
    long long dup = 0;
    for (int i = 0; i < csr->n; i++)
        for (int k = csr->row_ptr[i] + 1; k < csr->row_ptr[i + 1]; k++)
            dup += (csr->col_idx[k] == csr->col_idx[k - 1]);
    return dup;
}

static int row_contains(const struct CSRMatrix* csr, int row, int col) {
    int lo = csr->row_ptr[row], hi = csr->row_ptr[row + 1] - 1;   // binary search, sorted row
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (csr->col_idx[mid] == col) return 1;
        if (csr->col_idx[mid] < col) lo = mid + 1; else hi = mid - 1;
    }
    return 0;
}

long long csr_pattern_asymmetry(const struct CSRMatrix* csr) {
    long long missing = 0;
    for (int i = 0; i < csr->n; i++)
        for (int k = csr->row_ptr[i]; k < csr->row_ptr[i + 1]; k++) {
            int j = csr->col_idx[k];
            if (j != i && !row_contains(csr, j, i)) missing++;
        }
    return missing;
}
