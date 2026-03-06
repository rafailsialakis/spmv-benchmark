#include "csr.h"
#include <stdio.h>
#include <metis.h>
#include <stdlib.h>
#include <suitesparse/cs.h>
#ifndef REORDER_H
#define REORDER_H

typedef enum {
    REORDER_NONE,
    REORDER_RCM,
    REORDER_METIS
} ReorderType;

/*
 * Computes a permutation vector using RCM (via SuiteSparse).
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
 * Computes a permutation vector using METIS nested dissection.
 *
 * Args:
 *     csr (struct CSRMatrix*): Input matrix.
 *
 * Returns:
 *     Permutation vector p[] of size csr->n.
 *     Caller is responsible for freeing it.
 */
int* compute_permutation_metis(struct CSRMatrix* csr);

/*
 * Applies a permutation vector to a CSR matrix (A' = P·A·Pᵀ).
 *
 * Args:
 *     csr (struct CSRMatrix*): Input matrix.
 *     p (int*): Permutation vector of size csr->n.
 *
 * Returns:
 *     New permuted CSRMatrix. 
 * 
 * Note:
 *     Caller is responsible for freeing it with csr_free().
 */
struct CSRMatrix* permute_csr(struct CSRMatrix* csr, int* p);

#endif