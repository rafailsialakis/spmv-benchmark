#include <stdio.h>
#include <stdlib.h>
#include "../include/coo.h"
#include "../include/csr.h"

struct CSRMatrix* csr_from_coo(struct COOMatrix* coo_mtx){
    struct CSRMatrix* csr_mtx = (struct CSRMatrix*) malloc(sizeof(struct CSRMatrix));
    csr_mtx->n = coo_mtx->metadata.rows;
    csr_mtx->nnz = coo_mtx->metadata.nnz;
    csr_mtx->row_ptr = (int*) calloc(csr_mtx->n,sizeof(int));
    csr_mtx->col_idx = (int*) malloc(sizeof(int) * (csr_mtx->nnz));
    csr_mtx->values = (double*) malloc(sizeof(double) * (csr_mtx->nnz));
    for (int i = 0; i < csr_mtx->nnz; i++){
        csr_mtx->row_ptr[coo_mtx->row_idx[i] + 1]++;
    }
    for(int i = 1; i <= csr_mtx->n; i++){
        csr_mtx->row_ptr[i] += csr_mtx->row_ptr[i-1];
    }
    int* cursor = calloc(csr_mtx->n, sizeof(int));
    for(int k = 0; k < csr_mtx->nnz; k++){
        int row = coo_mtx->row_idx[k];
        int pos = csr_mtx->row_ptr[row] + cursor[row]++;
        csr_mtx->col_idx[pos] = coo_mtx->col_idx[k];
        csr_mtx->values[pos] = csr_mtx->values[k];\
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