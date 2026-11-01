#include <math.h>
#include <omp.h>
#include "spmv/spmv.h"
#include "matrix/csr.h"
#include "benchmark/timer.h"
#include "benchmark/benchmark.h"

double compute_gflops(int nnz, double time_sec) {
    return (2.0 * nnz) / (time_sec * 1e9);
}

void flush_cache() {
    volatile char* buffer = (volatile char*) malloc(FLUSH_BYTES);
    if (!buffer) {
        fprintf(stderr, "flush_cache: allocation failed\n");
        exit(EXIT_FAILURE);
    }
    // Same static schedule and thread count as the kernel that follows.
    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < FLUSH_BYTES; i += 64)
        buffer[i] = (char)i;
    free((void*)buffer);
}

int count_nonnormal(const double* v, int n) {
    int bad = 0;
    for (int j = 0; j < n; j++) {
        int c = fpclassify(v[j]);
        bad += (c == FP_SUBNORMAL || c == FP_INFINITE || c == FP_NAN);
    }
    return bad;
}

static double median(double* arr, int n) {
    // Insertion sort
    for (int i = 1; i < n; i++) {
        double key = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j+1] = arr[j];
            j--;
        }
        arr[j+1] = key;
    }
    if (n % 2 == 0)
        return (arr[n/2 - 1] + arr[n/2]) / 2.0;
    return arr[n/2];
}

BenchResult run_benchmark_cold(const char* label, struct CSRMatrix* csr, double* x, double* y) {
    for (int i = 0; i < csr->n; i++) x[i] = 1;
    flush_cache();
    double start = get_time();
    spmv_csr_parallel(csr, x, y);
    double end = get_time();
    double time = end - start;
    BenchResult r;
    r.time_ms = time * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, time);
    r.nonnormal = -1;
    printf("%s\t%s\t%.6f\t%.4f\n", "COLD", label, r.time_ms, r.gflops);
    return r;
}

BenchResult run_benchmark_rax(const char* label, struct CSRMatrix* csr,
                               double* x, double* y) {
    double times[N_RUNS];
    for (int i = 0; i < csr->n; i++) x[i] = 1;
    for (int i = 0; i < WARMUP_RUNS; i++)
        spmv_csr_parallel(csr, x, y);
    for (int i = 0; i < N_RUNS; i++) {
        double start = get_time();
        spmv_csr_parallel(csr, x, y);
        double end = get_time();
        times[i] = end - start;
    }
    double t = median(times, N_RUNS);
    BenchResult r;
    r.time_ms = t * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, t);
    r.nonnormal = -1;
    printf("%s\t%s\t%.6f\t%.4f\n", "RAX", label, r.time_ms, r.gflops);
    return r;
}

BenchResult run_benchmark_ios(const char* label, struct CSRMatrix* csr, double* x, double* y) {
    double times[N_RUNS];
    double *in = x, *out = y;
    for (int j = 0; j < csr->n; j++) x[j] = 1;
    for (int i = 0; i < N_RUNS; i++) {
        double start = get_time();
        spmv_csr_parallel(csr, in, out);
        double end = get_time();
        times[i] = end - start;
        double *tmp = in; in = out; out = tmp;
    }
    double t = median(times, N_RUNS);
    BenchResult r;
    r.time_ms = t * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, t);
    // After the last swap, `in` holds the most recent output vector.
    r.nonnormal = count_nonnormal(in, csr->n);
    if (r.nonnormal > 0)
        fprintf(stderr, "WARNING IOS [%s]: %d subnormal/inf/NaN entries in the final vector\n",
                label, r.nonnormal);
    printf("%s\t%s\t%.6f\t%.4f\n", "IOS", label, r.time_ms, r.gflops);
    return r;
}