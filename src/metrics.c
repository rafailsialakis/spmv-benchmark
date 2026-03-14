#include <stdio.h>
#include <stdlib.h>
#include "../include/csr.h"
#include "../include/metrics.h"

int compute_bandwidth(struct CSRMatrix* csr){
    int max_bandwidth = -1;
    for(int i = 0; i < csr->n; i++){
        for(int j = csr->row_ptr[i]; j < csr->row_ptr[i+1]; j++){
            int col = csr->col_idx[j];
            int bw = abs(i - col);
            if(bw > max_bandwidth){
                max_bandwidth = bw;
            }
        }
    }
    return max_bandwidth;
}

double compute_density(struct CSRMatrix* csr){
    return (double) csr->nnz / ((double)csr->n * csr->n);
}

double compute_imbalance_ratio(struct CSRMatrix* csr, int threads){
    int max_nnz_thread = 0;
    int rows_per_thread = csr->n / threads;
    for(int t = 0; t < threads; t++){
        int row_start = t * rows_per_thread;
        int row_end = (t + 1) * rows_per_thread;
        if (t == (threads - 1))
            row_end = csr->n;
        int nnz_thread = csr->row_ptr[row_end] - csr->row_ptr[row_start];
        if(nnz_thread > max_nnz_thread){
            max_nnz_thread = nnz_thread;
        }
    }
    return (double)max_nnz_thread / ((double)csr->nnz / threads);
}