#include <stdio.h>
#include <stdlib.h>
#include <float.h>
#include "../include/csr.h"
#include "../include/spmv.h"
#include "../include/timer.h"
#include "../include/benchmark.h"

double compute_gflops(int nnz, double time_sec) {
    return (2.0 * nnz) / (time_sec * 1e9);
}

void flush_cache(){
    size_t size = 64 * 1024 * 1024; // 64MB
    char* buffer = (char*) malloc(size);
    for(int i = 0; i < size; i+=64){
        buffer[i]++;
    }
    free(buffer);
}

BenchResult run_benchmark_cold(const char* label, struct CSRMatrix* csr, double* x, double* y){
    double best_time = DBL_MAX;
    for(int i = 0; i < N_RUNS; i++){
        flush_cache();
        double start = get_time();
        spmv_csr(csr, x, y);
        double end = get_time();
        double t = end - start;
        if (t < best_time) best_time = t;
    }
    BenchResult r;
    r.time_ms = best_time * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, best_time);
    printf("%s\t%s\t%.3f\t%.2f\n","COLD", label, r.time_ms, r.gflops);
    return r;
}

BenchResult run_benchmark_rax(const char* label, struct CSRMatrix* csr, double* x, double* y) {
    double best_time = DBL_MAX;
    for(int i = 0; i < WARMUP_RUNS; i++)        
        spmv_csr(csr, x, y);
    for (int i = 0; i < N_RUNS; i++) {
        double start = get_time();
        spmv_csr(csr, x, y);
        double end = get_time();
        double t = end - start;
        if (t < best_time) best_time = t;
    }
    BenchResult r;
    r.time_ms = best_time * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, best_time);
    printf("%s\t%s\t%.3f\t%.2f\n","RAX", label, r.time_ms, r.gflops);
    return r;
}

BenchResult run_benchmark_ios(const char* label, struct CSRMatrix* csr, double* x, double* y) {
    double best_time = DBL_MAX;
    for (int i = 0; i < N_RUNS; i++) {
        double start, end, t;
        if (i % 2 == 0) {
            start = get_time();
            spmv_csr(csr, x, y);
            end = get_time();
        } else {
            start = get_time();
            spmv_csr(csr, y, x);
            end = get_time();
        }
        t = end - start;
        if (t < best_time) best_time = t;
    }
    BenchResult r;
    r.time_ms = best_time * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, best_time);
    printf("%s\t%s\t%.3f\t%.2f\n","IOS", label, r.time_ms, r.gflops);
    return r;
}