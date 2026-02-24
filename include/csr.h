#ifndef CSR_H
#define CSR_H
#include "coo.h"

/*
* This struct represents the format of a Compressed Sparse Row matrix.
*
* Fields:
*     n (long): The number of rows the matrix has.
*     cols (long): The number of columns the matrix has.
*     nnz (long): The number of non-zero elements.
*/
struct CSRMatrix{
    int    n;      
    int    nnz;    
    int   *row_ptr;
    int   *col_idx;
    double *values;
};

/*
 * Transforms a sparse matrix from COO format to CSR format.
 * 
 * The conversion is done in 3 steps:
 *   1. Count the number of non-zeros per row
 *   2. Compute the prefix sum to build row_ptr
 *   3. Fill col_idx and values using a cursor array
 *      that tracks the current insertion position per row
 *
 * Args:
 *     coo_mtx (struct COOMatrix*): Pointer to the source matrix in COO format.
 *                                  Must have metadata (rows, cols, nnz) initialized
 *                                  and row_idx, col_idx, values allocated.
 *
 * Returns:
 *     Pointer to a newly allocated CSRMatrix.
 *     The caller is responsible for freeing it with csr_free().
 *
 * Notes:
 *     - Assumes 0-based indices in the COO matrix.
 *     - The COO matrix does not need to be sorted by row.
 */
struct CSRMatrix* csr_from_coo(struct COOMatrix* coo_mtx);
void csr_free(struct CSRMatrix* csr);

#endif