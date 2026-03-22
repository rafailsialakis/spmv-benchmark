#include   "coo.h"

#ifndef    CSR_H
#define    CSR_H

/*
 * Represents the format of a Compressed Sparse Row matrix.
 *
 * Fields:
 *     n (int): The number of rows the matrix has
 *     nnz (int): The number of non-zero elements
 *     row_ptr (int*): Points to the next non-zero element
 *     col_idx (int*): Array with column indics
 *     values (double*): Array with the values  
 */
struct CSRMatrix{
    int     n;      
    int     nnz;    
    int    *row_ptr;
    int    *col_idx;
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

/*
 * Used to free the fields of the csr struct and the struct itself.
 * 
 * Args: 
 *     csr (struct CSRMatrix*): Pointer to a CSR Matrix struct that will be freed.
 */
void csr_free(struct CSRMatrix* csr);

#endif