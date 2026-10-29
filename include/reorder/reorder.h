#include   <stdio.h>
#include   <stdint.h>
#include   <scotch.h>
#include   <stdlib.h>
#include   <stdbool.h>
#include   "matrix/csr.h"
#include   <suitesparse/cs.h>

#ifndef    REORDER_H
#define    REORDER_H
#define    SCOTCH_SEED 1    // Fixed seed so that ND and GP are reproducible
#define    GP_PARTS    4    // Number of k-way partitions (= max thread count)
#define    GP_IMBALANCE 0.03 // Allowed load imbalance (as METIS default ufactor = 30)

/*
 * Computes a permutation vector using Reverse Cuthill-McKee
 * (genrcm, third-party/rcm by J. Burkardt, MIT license).
 *
 * Args:
 *     csr (struct CSRMatrix*): Input matrix.
 *
 * Returns:
 *     Permutation vector p[] of size csr->n.
 *     Caller is responsible for freeing it.
 */
int* compute_permutation_rcm(struct CSRMatrix* csr);

/*
 * Computes a permutation vector using AMD (via CXSparse).
 *
 * Args:
 *     csr (struct CSRMatrix*): Input matrix.
 *
 * Returns:
 *     Permutation vector p[] of size csr->n.
 *     Caller is responsible for freeing it.
 */
int* compute_permutation_amd(struct CSRMatrix* csr);

/*
 * Computes a permutation vector using Scotch nested dissection
 * (deterministic Scotch context, fixed seed).
 *
 * Args:
 *     csr (struct CSRMatrix*): Input matrix.
 *
 * Returns:
 *     Permutation vector p[] of size csr->n.
 *     Caller is responsible for freeing it.
 */
int* compute_permutation_nd(struct CSRMatrix* csr);

/*
 * Computes a permutation vector using Scotch k-way graph partitioning
 * into GP_PARTS parts (deterministic Scotch context, fixed seed). Rows are grouped by part; within a part the
 * original relative order is kept.
 *
 * Args:
 *     csr (struct CSRMatrix*): Input matrix.
 *
 * Returns:
 *     Permutation vector p[] of size csr->n.
 *     Caller is responsible for freeing it.
 */
int* compute_permutation_gp(struct CSRMatrix* csr);

/*
 * Applies a permutation vector to a CSR matrix (A' = P·A·Pᵀ).
 *
 * Args:
 *     csr (struct CSRMatrix*): Input matrix.
 *     p (int*):                Permutation vector of size csr->n.
 *
 * Returns:
 *     New permuted CSRMatrix. Column indices within each row are sorted
 *     in ascending order.
 *
 * Note:
 *     Caller is responsible for freeing it with csr_free().
 */
struct CSRMatrix* permute_csr(struct CSRMatrix* csr, int* p);

#endif