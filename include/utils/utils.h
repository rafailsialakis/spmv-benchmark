#include <papi.h>
#include <stdio.h>

#ifndef UTILS_H
#define UTILS_H

#if defined(__aarch64__)
    #define PLATFORM_NAME "arm"
    #define RESULTS_DIR   "arm_results"
#elif defined(__x86_64__)
    #define PLATFORM_NAME "x86"
    #define RESULTS_DIR   "x86_results"
#else
    #error "Unsupported platform"
#endif

#define MAX_NUM_THREADS 4

/*
 * Specifies the path of the *.mtx file. The path is: matrices/<field>/<matrix_file>
 * The matrices folder is not passed in the function, just <field>/<matrix_file>.
 *
 * Fields:
 *     folder (const char*): Specifies the field of the matrix (e.g. FEM, CFD)
 *     file   (const char*): Specifies the name of the file (e.g. Geo_1438)
 */
struct Path {
    const char* folder;
    const char* file;
};

/*
 * Defines the permutation vectors for each reordering method.
 *
 * Fields:
 *     rcm_perm (int*): Permutation vector for RCM
 *     amd_perm (int*): Permutation vector for AMD
 *     nd_perm  (int*): Permutation vector for METIS (ND)
 */
struct Permutations {
    int* rcm_perm;
    int* amd_perm;
    int* nd_perm;
};

/*
 * Used in order to ensure that the reordering in SpMxV produces the same
 * results as SpMxV with no reordering.
 * More specifically: y' = A'*Px = (PAP^T)*Px = PA*(P^T*Px) = PAx = Py
 *                    y  = P^T * y'
 *
 * Args:
 *     original  (struct CSRMatrix*): Pointer to the original CSR matrix
 *     reordered (struct CSRMatrix*): Pointer to the reordered CSR matrix
 *     p         (int*):             The permutation vector applied
 *     label     (const char*):      Reordering method label
 */
void assert_permutation_correct(struct CSRMatrix* original,
                                struct CSRMatrix* reordered,
                                int* p, const char* label);

/*
 * Exports permutation vectors to .txt files for sparsity pattern plotting.
 *
 * Args:
 *     csr  (struct CSRMatrix*):    Pointer to the parsed CSR matrix
 *     perm (struct Permutations*): Pointer to the permutation vectors struct
 *
 * Note:
 *     NOT used in normal execution — only for generating sparsity patterns.
 *     Exits the program with status code 1.
 */
void export_permutations(struct CSRMatrix* csr, struct Permutations* perm);

/*
 * Opens (or creates) a CSV file at the given path with the specified header.
 * Appends if file exists, writes header if newly created.
 *
 * Args:
 *     path   (const char*): Path where the file will be opened/created
 *     header (const char*): Comma-separated column headers
 *
 * Returns:
 *     FILE*: Pointer to the opened file
 */
FILE* open_csv(const char* path, const char* header);

/*
 * Splits argv[1] into folder and filename. E.g. "FEM/Geo_1438.mtx" →
 *     folder: "FEM"
 *     file:   "Geo_1438"
 *
 * Args:
 *     arg (char*): The argument passed to the program
 *
 * Returns:
 *     struct Path*: Pointer to the populated Path struct
 */
struct Path* split_path(char* arg);

/*
 * Parses a *.mtx file and converts it to CSR format:
 *   1. Parse *.mtx → COO
 *   2. COO → CSR
 *
 * Args:
 *     path (char*): Path to the matrix file
 *
 * Returns:
 *     struct CSRMatrix*: Pointer to the parsed CSR matrix
 */
struct CSRMatrix* read_matrix(char* path);

/*
 * Computes permutation vectors for RCM, AMD and METIS (ND).
 * Also records reordering times in RESULTS_DIR/reorder_times.csv.
 *
 * Args:
 *     csr  (struct CSRMatrix*): Pointer to the CSR matrix to reorder
 *     name (const char*):       Matrix name (used for CSV logging)
 *     save (int):               Save mode (1:yes / 0:no)
 * 
 * Returns:
 *     struct Permutations*: Pointer to the computed permutation vectors
 */
struct Permutations* compute_permutations(struct CSRMatrix* csr, const char* name, int save);

/*
 * Computes structural metrics for the original and reordered matrices
 * (bandwidth, average bandwidth, imbalance ratio, density, etc.)
 * and writes them to RESULTS_DIR/metrics.csv.
 *
 * Args:
 *     csr     (struct CSRMatrix*): Pointer to the original CSR matrix
 *     csr_rcm (struct CSRMatrix*): Pointer to the RCM-reordered matrix
 *     csr_amd (struct CSRMatrix*): Pointer to the AMD-reordered matrix
 *     csr_nd  (struct CSRMatrix*): Pointer to the ND-reordered matrix
 *     path    (struct Path*):      Pointer to the path struct
 */
void compute_matrix_metrics(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm,
                             struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd,
                             struct Path* path);

/*
 * Runs RAx, IOs and Cold Cache benchmarks for all reorderings,
 * at 1, 2 and 4 threads. Results saved to RESULTS_DIR/{rax,ios,cold}.csv.
 *
 * Args:
 *     csr     (struct CSRMatrix*): Pointer to the original CSR matrix
 *     csr_rcm (struct CSRMatrix*): Pointer to the RCM-reordered matrix
 *     csr_amd (struct CSRMatrix*): Pointer to the AMD-reordered matrix
 *     csr_nd  (struct CSRMatrix*): Pointer to the ND-reordered matrix
 *     path    (struct Path*):      Pointer to the path struct
 */
void run_all_benchmarks(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm,
                        struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd,
                        struct Path* path);

/*
 * Runs cache miss benchmarks (L1, L2, and L3 on x86 only) sequentially
 * using the RAx methodology. Results saved to RESULTS_DIR/cache.csv.
 *
 * Args:
 *     csr     (struct CSRMatrix*): Pointer to the original CSR matrix
 *     csr_rcm (struct CSRMatrix*): Pointer to the RCM-reordered matrix
 *     csr_amd (struct CSRMatrix*): Pointer to the AMD-reordered matrix
 *     csr_nd  (struct CSRMatrix*): Pointer to the ND-reordered matrix
 *     path    (struct Path*):      Pointer to the path struct
 */
void run_cache_benchmarks(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm,
                          struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd,
                          struct Path* path);

/*
 * Runs TLB benchmarks (DTLB loads, DTLB load misses, ITLB load misses)
 * sequentially using the RAx methodology. Also computes the DTLB miss rate
 * as misses/loads. Results saved to RESULTS_DIR/tlb.csv.
 *
 * Note:
 *     Events are resolved at runtime via PAPI_event_name_to_code.
 *     If any event is unsupported on the target platform, the benchmark
 *     is skipped gracefully.
 *
 * Args:
 *     csr     (struct CSRMatrix*): Pointer to the original CSR matrix
 *     csr_rcm (struct CSRMatrix*): Pointer to the RCM-reordered matrix
 *     csr_amd (struct CSRMatrix*): Pointer to the AMD-reordered matrix
 *     csr_nd  (struct CSRMatrix*): Pointer to the ND-reordered matrix
 *     path    (struct Path*):      Pointer to the path struct
 */
void run_tlb_benchmarks(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm,
                         struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd,
                         struct Path* path);

/*
 * Frees all dynamically allocated memory (matrices, permutations, path).
 *
 * Args:
 *     csr     (struct CSRMatrix*):  Pointer to the original CSR matrix
 *     csr_rcm (struct CSRMatrix*):  Pointer to the RCM-reordered matrix
 *     csr_amd (struct CSRMatrix*):  Pointer to the AMD-reordered matrix
 *     csr_nd  (struct CSRMatrix*):  Pointer to the ND-reordered matrix
 *     perm    (struct Permutations*): Pointer to the permutation vectors
 *     path    (struct Path*):        Pointer to the path struct
 */
void cleanup(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm,
             struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd,
             struct Permutations* perm, struct Path* path);

#endif