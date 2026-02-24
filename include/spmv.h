#ifndef SPMV_H
#define SPMV_H
#include "csr.h"

/*
 * Computes y = A * x using CSR format.
 *
 * Args:
 *     csr (struct CSRMatrix*): The sparse matrix in CSR format.
 *     x (double*): Input vector of size csr->n.
 *     y (double*): Output vector of size csr->n.
 */
void spmv_csr(struct CSRMatrix* csr, double* x, double* y);

#endif