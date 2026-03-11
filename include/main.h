#include <stdio.h>
#ifndef MAIN_H
#define MAIN_H
#define MAX_NUM_THREADS 8

struct Path {
    const char* folder;
    const char* file;
};
FILE* open_csv(const char* path, const char* header);
struct Permutations{
    int* rcm_perm;
    int* amd_perm;
    int* metis_perm;
};

void compute_matrix_metrics(struct CSRMatrix* csr,
                        struct CSRMatrix* csr_rcm,
                        struct CSRMatrix* csr_amd,
                        struct CSRMatrix* csr_metis,
                        struct Path* path);

void run_all_benchmarks(struct CSRMatrix* csr,
                        struct CSRMatrix* csr_rcm,
                        struct CSRMatrix* csr_amd,
                        struct CSRMatrix* csr_metis,
                        struct Path* path);


void cleanup(struct CSRMatrix* csr,
             struct CSRMatrix* csr_rcm,
             struct CSRMatrix* csr_amd,
             struct CSRMatrix* csr_metis,
             struct Permutations* perm,
             struct Path* path);

struct Permutations* compute_permutations(struct CSRMatrix* csr, const char* name);
struct CSRMatrix* read_matrix(char* path);

struct Path* split_path(char* arg);
#endif