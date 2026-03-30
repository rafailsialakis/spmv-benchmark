#include   <stdio.h>

#ifndef    MAIN_H
#define    MAIN_H
#define    MAX_NUM_THREADS 4 

/*
 * Specifies the path of the *.mtx file. The path is: matrices/<field>/<matrix_file>
 * The matrices folder is not passed in the function, just <field>/<matrix_file>.
 * 
 * Fields:
 *     folder (const char*): Specifies the field of the matrix (e.g. FEM, CFD)
 *     file (const char*): Specifies the name of the file (e.g. Geo_1438.mtx) 
 */
struct Path {
    const char* folder;
    const char* file;
};

/*
 * Defines the permutation vectors for each reordering method.
 * 
 * Fields:
 *     rcm_perm (int*): Permutation vector for RCM Reordering method
 *     amd_perm (int*): Permutation vector for AMD Reordering method
 *     nd_perm (int*): Permutation vector for METIS Reordering method
 */
struct Permutations{
    int*    rcm_perm;
    int*    amd_perm;
    int*    nd_perm;
};

/* 
 * Used in order to ensure that the reordering in SpMxV produces the same results with SpMxV no reordering
 * More specifically: y' = A' * Px = (PAP^T) * Px = PA * (P^T*Px) = PAx = Py
 * y = P^-1 * y' = P^T * y'
 *
 * Args:
 *     original (struct CSRMatrix*): A pointer to the original CSR Matrix
 *     reordered (struct CSRMatrix*): A pointer to the reordered CSR Matrix
 *     p (int*): The permutation vector applied
 *     label (const char*): Reordering method label
 *
 */
void assert_permutation_correct(struct CSRMatrix* original, struct CSRMatrix* reordered, int* p, const char* label);

/*
 * Used to export the permutation vector into a .txt file specified by the given path
 *
 * Args:
 *     csr (struct CSRMatrix*): A pointer to the parsed CSR Matrix
 *     perm (struct Permutations*): A pointer to the struct with the saved permutation vectors
 * 
 * Note:
 *     This function is NOT used, is created in order to generate sparsity patterns. Ignore any warnings!
 *     This function exits the program with status code 1
 */
void export_permutations(struct CSRMatrix* csr, struct Permutations* perm);


/*
 * Used to open a *.csv file with a specified header.
 * 
 * Args:
 *     path (const char*): The path where the file will be opened/created
 *     header (const char*): A String that contains comma separated headers (e.g. name,last_name,age)
 * 
 * Returns:
 *     csv (FILE*): A pointer to the file that has been successfully created.
 */
FILE* open_csv(const char* path, const char* header);

/*
 * Splits the path used as argv[1]. E.g FEM/Geo_1438.mtx:
 * Field: FEM
 * Name: Geo_1438.mtx
 * 
 * Args:
 *     arg (char*): An argument the program is given
 * 
 * Returns:
 *     path_struct (Path*): A pointer to a Path
 */
struct Path* split_path(char* arg);

/*
 * Does all the mmio operations:
 * 1. Parses *.mtx file
 * 2. *.mtx to COO format
 * 3. COO format to CSR format
 * 
 * Args: 
 *     path (char*): The path to the matrix
 * 
 * Returns:
 *     csr (struct CSRMatrix*): A pointer to the parsed CSR Matrix
 */
struct CSRMatrix* read_matrix(char* path);

/*
 * Computes the permutation vectors for each reordering method
 * (RCM, AMD, METIS) based on the given CSR matrix.
 * 
 * Args:
 *     csr (struct CSRMatrix*): Pointer to the CSR matrix that will be reordered
 *     name (const char*): The name of the matrix file (used for logging/output)
 * 
 * Returns:
 *     perm (struct Permutations*): A pointer to a structure that contains
 *     the permutation vectors for RCM, AMD and METIS.
 */
struct Permutations* compute_permutations(struct CSRMatrix* csr, const char* name);

/*
 * Computes various matrix metrics for the original matrix and
 * for each reordered version (RCM, AMD, METIS).
 * These metrics may include bandwidth, profile, sparsity statistics, etc.
 * 
 * Args:
 *     csr (struct CSRMatrix*): Pointer to the original CSR matrix
 *     csr_rcm (struct CSRMatrix*): Pointer to the matrix reordered with RCM
 *     csr_amd (struct CSRMatrix*): Pointer to the matrix reordered with AMD
 *     csr_nd (struct CSRMatrix*): Pointer to the matrix reordered with METIS
 *     path (struct Path*): Pointer to the structure containing folder and file name
 */
void compute_matrix_metrics(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm, struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd, struct Path* path);

/*
 * Runs all performance benchmarks for the original matrix and
 * the reordered matrices (RCM, AMD, METIS). Benchmarks may include
 * operations such as SpMV, solver performance, or other matrix kernels.
 * 
 * Args:
 *     csr (struct CSRMatrix*): Pointer to the original CSR matrix
 *     csr_rcm (struct CSRMatrix*): Pointer to the RCM reordered matrix
 *     csr_amd (struct CSRMatrix*): Pointer to the AMD reordered matrix
 *     csr_nd (struct CSRMatrix*): Pointer to the METIS reordered matrix
 *     path (struct Path*): Pointer to the structure containing matrix path information
 */
void run_all_benchmarks(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm, struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd, struct Path* path);

/*
 * Frees all dynamically allocated memory used throughout the program.
 * This includes matrices, permutation vectors and path structures.
 * 
 * Args:
 *     csr (struct CSRMatrix*): Pointer to the original CSR matrix
 *     csr_rcm (struct CSRMatrix*): Pointer to the RCM reordered matrix
 *     csr_amd (struct CSRMatrix*): Pointer to the AMD reordered matrix
 *     csr_nd (struct CSRMatrix*): Pointer to the METIS reordered matrix
 *     perm (struct Permutations*): Pointer to the structure containing permutation vectors
 *     path (struct Path*): Pointer to the path structure
 */
void cleanup(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm, struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd, struct Permutations* perm, struct Path* path);


#endif