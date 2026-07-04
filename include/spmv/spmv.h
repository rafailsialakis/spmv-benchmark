#include   <omp.h>
#include   "matrix/csr.h"

#ifndef    SPMV_H
#define    SPMV_H

/*
 * Computes y = A * x using CSR format. Runs sequentially.
 *
 * Args:
 *     csr (struct CSRMatrix*): The sparse matrix in CSR format.
 *     x (double*):             Input vector of size csr->n.
 *     y (double*):             Output vector of size csr->n.
 */
void spmv_csr(struct CSRMatrix* csr, double* x, double* y);

/*
 * Computes y = A * x using CSR format. It runs in parallel using omp static scheduling.
 *
 * Args:
 *     csr (struct CSRMatrix*): The sparse matrix in CSR format.
 *     x (double*):             Input vector of size csr->n.
 *     y (double*):             Output vector of size csr->n.
 */
void spmv_csr_parallel(struct CSRMatrix* csr, double* x, double* y);

#endif