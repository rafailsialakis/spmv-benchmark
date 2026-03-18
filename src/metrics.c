#include "../include/csr.h"
#include "../include/metrics.h"

struct BWResult compute_bandwidth(struct CSRMatrix* csr){
    struct BWResult bandwidth_result;
    bandwidth_result.max_bw = -1;
    bandwidth_result.avg_bw = 0;
    long long bw_sum = 0;
    for(int i = 0; i < csr->n; i++){
        for(int j = csr->row_ptr[i]; j < csr->row_ptr[i+1]; j++){
            int col = csr->col_idx[j];
            int bw = abs(i - col);
            if(bw > bandwidth_result.max_bw){
                bandwidth_result.max_bw = bw;
            }
            bw_sum += bw;
        }
    }
    bandwidth_result.avg_bw = (double)bw_sum / csr->nnz;
    return bandwidth_result;
}

double compute_density(struct CSRMatrix* csr){
    return (double) csr->nnz / ((double)csr->n * csr->n);
}

double avg_nnz_row(struct CSRMatrix* csr){
    return (double) csr->nnz / (double) csr->n;
}

double std_nnz_row(struct CSRMatrix* csr){
    int nnz;
    double avg = avg_nnz_row(csr);
    double sum = 0;
    for(int i = 0; i < csr->n; i++){
        nnz = csr->row_ptr[i+1] - csr->row_ptr[i];
        sum += (nnz - avg) * (nnz - avg);
    }
    return sqrt(sum / (double)csr->n);
}

double compute_imbalance_ratio(struct CSRMatrix* csr, int threads){
    int max_nnz_thread = 0;
    int rows_per_thread = csr->n / threads;
    for(int t = 0; t < threads; t++){
        int row_start = t * rows_per_thread;
        int row_end = (t == threads-1) ? csr->n : (t+1) * rows_per_thread;
        int nnz_thread = csr->row_ptr[row_end] - csr->row_ptr[row_start];
        if(nnz_thread > max_nnz_thread)
            max_nnz_thread = nnz_thread;
    }
    return (double)max_nnz_thread / ((double)csr->nnz / threads);
}