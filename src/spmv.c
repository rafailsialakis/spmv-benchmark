#include "../include/csr.h"
#include "../include/spmv.h"

void spmv_csr(struct CSRMatrix* csr, double* x, double* y) {
    // Parallel for over rows
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < csr->n; i++) {
        double sum = 0.0;
        for (int j = csr->row_ptr[i]; j < csr->row_ptr[i+1]; j++) {
            sum += csr->values[j] * x[csr->col_idx[j]];
        }
        y[i] = sum;
     }
}