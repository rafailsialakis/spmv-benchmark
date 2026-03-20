#include   <stdio.h>
#include   <float.h>
#include   "../include/csr.h"

#ifndef    BENCHMARK_H
#define    BENCHMARK_H
#define    N_RUNS 100
#define    WARMUP_RUNS 5

/* Represents the result of a Benchmark: 
 * 
 * Fields:
 *     gflops (double): Giga floating point operations / second
 *     time (double): Time taken for SPMxV to execute
 */
typedef struct {
    double     gflops;
    double     time_ms;
} BenchResult;

/* Allocates 64MB of heap space, iterates them and frees the memory used.
 * 64MB > L1 (128KB) + L2 (2MB) + L3 (6MB) size 
 */
void flush_cache();

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