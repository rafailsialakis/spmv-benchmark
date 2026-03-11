#include "../include/csr.h"
#ifndef BENCHMARK_H
#define BENCHMARK_H
#define N_RUNS 100
#define WARMUP_RUNS 5

typedef struct {
    double gflops;
    double time_ms;
} BenchResult;
double compute_gflops(int nnz, double time_sec);
void flush_cache();
void print_result(int threads, const char* method, const char* reorder, BenchResult r);
BenchResult run_benchmark_cold(const char* label, struct CSRMatrix* csr, double* x, double* y);
BenchResult run_benchmark_rax(const char* label, struct CSRMatrix* csr, double* x, double* y);
BenchResult run_benchmark_ios(const char* label, struct CSRMatrix* csr, double* x, double* y);
#endif