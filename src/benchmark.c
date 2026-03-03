#include <stdio.h>
#include <stdlib.h>
#include <float.h>
#include "../include/csr.h"
#define N_RUNS 100

double compute_gflops(int nnz, double time_sec) {
    return (2.0 * nnz) / (time_sec * 1e9);
}

void run_benchmark(const char* label, struct CSRMatrix* csr, double* x, double* y) {
    double best_time = DBL_MAX;
    for (int i = 0; i < N_RUNS; i++) {
        double start = get_time();
        spmv_csr(csr, x, y);
        double end = get_time();
        double t = end - start;
        if (t < best_time) best_time = t;
    }

    double gflops = compute_gflops(csr->nnz, best_time);
    printf("%-20s time: %.3f ms   GFLOP/s: %.2f\n",
           label, best_time * 1000.0, gflops);
}