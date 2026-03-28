#include "../include/csr.h"
#include "../include/spmv.h"
#include "../include/timer.h"
#include "../include/benchmark.h"

double compute_gflops(int nnz, double time_sec) {
    return (2.0 * nnz) / (time_sec * 1e9);
}

void flush_cache() {
    size_t size = 256 * 1024 * 1024;
    volatile char* buffer = (volatile char*) malloc(size);
    if (!buffer) return;
    for (size_t i = 0; i < size; i += 64)
        buffer[i] = (char)i;
    free((void*)buffer);
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
    double times[N_RUNS];
    for (int i = 0; i < N_RUNS; i++) {
        flush_cache();
        double start = get_time();
        spmv_csr(csr, x, y);
        double end = get_time();
        times[i] = end - start;
    }
    double t = median(times, N_RUNS);
    BenchResult r;
    r.time_ms = t * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, t);
    printf("%s\t%s\t%.3f\t%.2f\n", "COLD", label, r.time_ms, r.gflops);
    return r;
}

BenchResult run_benchmark_rax(const char* label, struct CSRMatrix* csr,
                               double* x, double* y) {
    double times[N_RUNS];
    for (int i = 0; i < WARMUP_RUNS; i++)
        spmv_csr(csr, x, y);
    for (int i = 0; i < N_RUNS; i++) {
        double start = get_time();
        spmv_csr(csr, x, y);
        double end = get_time();
        times[i] = end - start;
    }
    double t = median(times, N_RUNS);
    BenchResult r;
    r.time_ms = t * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, t);
    printf("%s\t%s\t%.3f\t%.2f\n", "RAX", label, r.time_ms, r.gflops);
    return r;
}

BenchResult run_benchmark_ios(const char* label, struct CSRMatrix* csr, double* x, double* y) {
    double times[N_RUNS];
    double *in = x, *out = y;

    for (int i = 0; i < N_RUNS; i++) {
        double start = get_time();
        spmv_csr(csr, in, out);
        double end = get_time();
        times[i] = end - start;
        double *tmp = in; in = out; out = tmp;
    }
    double t = median(times, N_RUNS);
    BenchResult r;
    r.time_ms = t * 1000.0;
    r.gflops  = compute_gflops(csr->nnz, t);
    printf("%s\t%s\t%.3f\t%.2f\n", "IOS", label, r.time_ms, r.gflops);
    return r;
}