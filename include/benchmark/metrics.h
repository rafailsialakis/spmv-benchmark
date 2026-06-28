#include   <math.h>
#include   <stdlib.h>

#ifndef    METRICS_H
#define    METRICS_H

/*
 * Result of bandwidth calculation.
 *
 * Fields:
 *     max_bw (int): The max(|i-j|) of the matrix given.
 *     avg_bw (int): The Σi=0(|i-j|)/n.
 */
struct BWResult {
    int     max_bw;
    double  avg_bw;
};

/*
 * Calculates average non-zeros per row.
 *  
 * Args: 
 *     csr (struct CSRMatrix*): A pointer to the CSR Matrix
 *  
 * Returns:
 *     avg (double): Average non-zeros / row 
 */
double avg_nnz_row(struct CSRMatrix* csr);

/*
 * Calculates the standard deviation of the non-zeros per row.
 *
 * Args:
 *     csr (struct CSRMatrix*): A pointer to the CSR Matrix
 * 
 * Returns:
 *     std (double): Standard deviation of non-zeros / row
 */
double std_nnz_row(struct CSRMatrix* csr);

/*
 * Calculates matrix density based on the formula below: 
 * count_non-zero / (rows * cols)
 *
 * Args:
 *     csr (struct CSRMatrix*): A pointer to the CSR Matrix
 * 
 * Returns:
 *     density (double): The density of the matrix provided
 */
double compute_density(struct CSRMatrix* csr);

/*
 * Calculates how balanced the matrix is based on how many non zero elements
 * each thread processes. It is based on the formula:
 * max(nnz_per_thread) / avg(nnz_per_thread),
 * Where avg(nnz_per_thread) = count_nnz / threads
 *
 * Args:
 *     csr (struct CSRMatrix*): A pointer to the CSR Matrix
 *     threads (int): The number of threads used for SPMxV 
 * 
 * Returns:
 *     ratio (double): The imbalance ratio.
 * 
 * Note:
 *     A good imbalance ratio is near 1.00. The more it exceeds 1.00,
 *     the more unbalanced the matrix is. 
 */
double compute_imbalance_ratio(struct CSRMatrix* csr, int threads);

/*
 * Computes the average & max bandwidth of a (sparse) matrix.
 * 
 * Args:
 *     csr (struct CSRMatrix*): A pointer to the CSR Matrix
 * 
 * Returns:
 *     bw (struct BWResult): The avg and max bw.
 */
struct BWResult compute_bandwidth(struct CSRMatrix* csr);

#endif
