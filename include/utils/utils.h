#include <papi.h>
#include <stdio.h>

#ifndef UTILS_H
#define UTILS_H

#if defined(__aarch64__)
    #define PLATFORM_NAME "arm"
    #define RESULTS_DIR   "results/arm_results"
#elif defined(__x86_64__)
    #define PLATFORM_NAME "x86"
    #define RESULTS_DIR   "results/x86_results"
#else
    #error "Unsupported platform"
#endif

#define MAX_NUM_THREADS 4
#define N_REORDERINGS   5   // none, rcm, amd, nd, gp
#define N_METHODS       4   // rcm, amd, nd, gp (the reorderings, without the baseline)

// Labels in the order of struct MatrixSet.m: {"none", "rcm", "amd", "nd", "gp"}
extern const char* const REORDERING_NAMES[N_REORDERINGS];

/*
 * Specifies the path of the *.mtx file. The path is: matrices/<field>/<matrix_file>
 * The matrices folder is not passed in the function, just <field>/<matrix_file>.
 *
 * Fields:
 *     folder (const char*): Specifies the matrix category (e.g. Structural, CFD)
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
 *     rcm_perm (int*): Permutation vector for RCM (genrcm)
 *     amd_perm (int*): Permutation vector for AMD (CXSparse cs_amd)
 *     nd_perm  (int*): Permutation vector for Scotch nested dissection (ND)
 *     gp_perm  (int*): Permutation vector for Scotch k-way partitioning (GP)
 *     order_s  (double[N_METHODS]): Wall time (s) to compute each permutation,
 *                                   in the order rcm, amd, nd, gp
 *
 * All vectors use the convention p[new] = old.
 */
struct Permutations {
    int* rcm_perm;
    int* amd_perm;
    int* nd_perm;
    int* gp_perm;
    double order_s[N_METHODS];
};

/*
 * The five matrices that every benchmark mode compares.
 *
 * Fields:
 *     m       (struct CSRMatrix*[N_REORDERINGS]): none, rcm, amd, nd, gp.
 *             m[0] ("none") is the original ordering rebuilt with the identity
 *             permutation through permute_csr, so all five matrices are built by
 *             the same code (fresh allocation, sorted column indices).
 *     perm    (struct Permutations*): Permutation vectors and their compute times
 *     apply_s (double[N_METHODS]): Wall time (s) of permute_csr for each method
 *     path    (struct Path*): Matrix category and name
 */
struct MatrixSet {
    struct CSRMatrix*    m[N_REORDERINGS];
    struct Permutations* perm;
    double               apply_s[N_METHODS];
    struct Path*         path;
};

/*
 * Checks that the matrix (sorted columns) has no duplicate entries and a
 * structurally symmetric pattern. RCM, AMD and Scotch all treat the pattern
 * as an undirected graph; Scotch nested dissection does not terminate on an
 * unsymmetric one. Exits with an explanation if a check fails.
 */
void require_symmetric_pattern(const struct CSRMatrix* sorted, const char* name);

/*
 * Reads matrices/<arg>, checks the pattern (require_symmetric_pattern) before
 * any ordering runs, computes and validates all permutations, builds the five
 * matrices of a MatrixSet and frees the parsed original.
 * If save_times is 1, appends compute and apply times to RESULTS_DIR/reorder_times.csv.
 */
struct MatrixSet* prepare_matrices(char* arg, int save_times);

/* Frees everything owned by a MatrixSet. */
void free_matrix_set(struct MatrixSet* set);

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
 *     set (struct MatrixSet*): Matrices and permutation vectors
 *
 * Note:
 *     NOT used in normal execution — only for generating sparsity patterns.
 *     Exits the program with status code 1.
 */
void export_permutations(struct MatrixSet* set);

/*
 * Opens (or creates) a CSV file at the given path with the specified header.
 * Appends if file exists, writes header if newly created. Exits with an error
 * if an existing file has a different header (e.g. results from an older
 * version of the benchmark), so rows with different columns are never mixed.
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
 * Splits argv[1] into folder and filename. E.g. "Geomechanics/Geo_1438.mtx" →
 *     folder: "Geomechanics"
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
 * Computes permutation vectors for RCM, AMD, Scotch ND and Scotch k-way (GP),
 * checks that each is a valid permutation and records the compute times
 * in perm->order_s.
 *
 * Args:
 *     csr (struct CSRMatrix*): Pointer to the CSR matrix to reorder
 *
 * Returns:
 *     struct Permutations*: Pointer to the computed permutation vectors
 */
struct Permutations* compute_permutations(struct CSRMatrix* csr);

/*
 * Computes structural metrics for the original and reordered matrices
 * (bandwidth, average bandwidth, imbalance ratio, density, etc.)
 * and writes them to RESULTS_DIR/metrics.csv.
 *
 * Args:
 *     set (struct MatrixSet*): The five matrices and the matrix path
 */
void compute_matrix_metrics(struct MatrixSet* set);

/*
 * Runs RAx, IOs and Cold Cache benchmarks for all reorderings at 1, 2 and 4
 * threads, repeated SPMV_REPS times (default N_REPS). In every repetition and
 * thread count the order of the five matrices is shuffled (seeded by SPMV_SEED
 * and the matrix name, so a run is reproducible). Each CSV row records the
 * repetition (rep) and the position in the shuffled order (pos).
 * Results saved to RESULTS_DIR/{rax,ios,cold}.csv.
 *
 * Args:
 *     set (struct MatrixSet*): The five matrices and the matrix path
 */
void run_all_benchmarks(struct MatrixSet* set);

/*
 * Replays the IOs iteration sequence (x = 1, N_RUNS swaps) untimed and
 * serially on the baseline matrix and checks the output vector after every
 * iteration for subnormal, infinite or NaN entries. The parallel kernel computes
 * every row in the same order, so the timed runs see exactly these values.
 * A check of only the final vector would miss values that pass through the
 * subnormal range and then underflow to zero.
 * Results appended to RESULTS_DIR/ios_scan.csv; a warning is printed if any
 * iteration produced non-normal values.
 */
void ios_numeric_scan(struct MatrixSet* set);

/*
 * Runs cache miss benchmarks (L1, L2, and L3 on x86 only) sequentially
 * using the RAx methodology. Results saved to RESULTS_DIR/cache.csv.
 *
 * Args:
 *     set (struct MatrixSet*): The five matrices and the matrix path
 */
void run_cache_benchmarks(struct MatrixSet* set);

/*
 * Runs TLB benchmarks (DTLB load misses, ITLB load misses) sequentially
 * using the RAx methodology. Results saved to RESULTS_DIR/tlb.csv.
 *
 * Note:
 *     Events are resolved at runtime via PAPI_event_name_to_code.
 *     If any event is unsupported on the target platform, the benchmark
 *     is skipped gracefully.
 *
 * Args:
 *     set (struct MatrixSet*): The five matrices and the matrix path
 */
void run_tlb_benchmarks(struct MatrixSet* set);

#endif
