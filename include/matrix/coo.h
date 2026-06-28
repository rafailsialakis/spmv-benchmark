#include   <stdlib.h>

#ifndef    COO_H   
#define    COO_H

/*
* Represents the metadata information of a SuiteSparse .mtx file.
*
* Fields:
*     rows (long): The number of rows the matrix has.
*     cols (long): The number of columns the matrix has.
*     nnz (long):  The number of non-zero elements.
*/
struct Metadata {
    int    rows;
    int    cols;
    int    nnz;
};

/*
 * Represents the Coordinate Format of a Sparse Matrix.
 *
 * Fields:
 *     metadata (struct Metadata): Struct that contains information about the number of rows, cols and nnz.
 *     row_idx (long*):
 *     col_idx (long*):
 *     values (double*):
 */
struct COOMatrix {
    struct Metadata metadata;
    int            *row_idx;
    int            *col_idx;
    double         *values;
};

/*
 * This function is used to free memory allocated by the COOMatrix struct.
 *
 * Args:
 *     coo (struct COOMatrix*): The COOMatrix struct memory will be freed from.
 */
void coo_free(struct COOMatrix* coo);
#endif