#ifndef CSR_H
#define CSR_H
#include "coo.h"

struct CSRMatrix{
    int    n;        // αριθμός γραμμών/στηλών
    int    nnz;      // αριθμός non-zeros
    int   *row_ptr;  // μέγεθος n+1
    int   *col_idx;  // μέγεθος nnz
    double *values;  // μέγεθος nnz
};

struct CSRMatrix* csr_from_coo(struct COOMatrix* coo_mtx);
void csr_free(struct CSRMatrix* csr);

#endif