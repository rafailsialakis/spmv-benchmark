#include   <stdio.h>
#include   <float.h>
#include   "matrix/csr.h"

#ifndef    BENCHMARK_H
#define    BENCHMARK_H
#define    N_RUNS 100
#define    WARMUP_RUNS 5

// Independent repetitions of the whole (thread count x reordering) sweep per
// matrix, each with a freshly shuffled reordering order. Override at run time
// with the SPMV_REPS environment variable (SPMV_SEED sets the shuffle seed).
#ifndef    N_REPS
#define    N_REPS 5
#endif
#define    DEFAULT_SHUFFLE_SEED 20261029u

#if defined(__aarch64__)
    #define FLUSH_BYTES (64UL * 1024 * 1024)
#elif defined(__x86_64__)
    #define FLUSH_BYTES (16UL * 1024 * 1024)
#endif

/* Represents the result of a Benchmark: 
 * 
 * Fields:
 *     gflops (double): Giga floating point operations / second
 *     time (double): Time taken for SPMxV to execute
 */
typedef struct {
    double     gflops;
    double     time_ms;
    int        nonnormal;   // IOs only: subnormal/inf/NaN entries in the final vector (-1 = not checked)
} BenchResult;

/* Writes FLUSH_BYTES of a fresh buffer from all threads of the current team
 * (64 MiB on ARM > 32 MiB L3, 16 MiB on x86 > 6 MiB L3). Each thread touches its
 * own contiguous chunk, so the private L1/L2 of every core used by the kernel
 * are evicted as well, not only those of the calling core.
 */
void flush_cache();

/* Counts entries of v that are subnormal, infinite or NaN. */
int count_nonnormal(const double* v, int n);

/* Used to calculate GFLOP/s
 * 
 * Args:
 *     nnz (int): Total count of non-zero elements
 *     time_sec (double): Time in seconds
 *
 * Returns:
 *     gflops (double): Giga Floating Point Operations / Second
 */
double compute_gflops(int nnz, double time_sec);

/* Runs the benchmark using a cold cache.
 * At first, the cache is flushed and after the SPMxV is executed and measured
 * in order to simulate a cold cache execution.
 * 
 * Args:
 *     label (const char*): A pointer to a character array that represents the reordering methodology.
 *     csr (struct CSRMatrix*): A pointer to the CSR matrix used in the benchmark.
 *     x (double*): A pointer to a vector x  
 *     y (double*): A pointer to a vector y  
 *
 * Returns:
 *     result (struct Benchresult): A benchresult that contains GFLOP/s and T(ms).
 */
BenchResult run_benchmark_cold(const char* label, struct CSRMatrix* csr, double* x, double* y);

/* Runs the benchmark using Repeated Ax measure methodology. 
 * This methodology is based on the equation y = A*x where A*x is repeated.
 * First run WARMUP_RUNS SPMxV and after run N_RUNS iterations with a 
 * warm cache in order to maximize cache references. 
 * 
 * Args:
 *     label (const char*): A pointer to a character array that represents the reordering methodology.
 *     csr (struct CSRMatrix*): A pointer to the CSR matrix used in the benchmark.
 *     x (double*): A pointer to a vector x  
 *     y (double*): A pointer to a vector y  
 *
 * Returns:
 *     result (struct Benchresult): A benchresult that contains GFLOP/s and T(ms).
 */
BenchResult run_benchmark_rax(const char* label, struct CSRMatrix* csr, double* x, double* y);

/* Runs the benchmark using the Input Output swap measure methodology. 
 * This methodology is based on swapping the vector x with the vector y.
 * So we repeat the executions of the equations: y = A*x and x = A*y.
 * This simulates the behaviour of many iterative algorithms. 
 * 
 * Args:
 *     label (const char*): A pointer to a character array that represents the reordering methodology.
 *     csr (struct CSRMatrix*): A pointer to the CSR matrix used in the benchmark.
 *     x (double*): A pointer to a vector x  
 *     y (double*): A pointer to a vector y  
 *
 * Returns:
 *     result (struct Benchresult): A benchresult that contains GFLOP/s and T(ms).
 */
BenchResult run_benchmark_ios(const char* label, struct CSRMatrix* csr, double* x, double* y);
#endif