#include "../include/csr.h"
#include "../include/spmv.h"
#include "../include/main.h"
#include "../include/timer.h"
#include "../include/parser.h"
#include "../include/metrics.h"
#include "../include/reorder.h"
#include "../include/benchmark.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <file.mtx>\n", argv[0]);
        return EXIT_FAILURE;
    }
    setenv("OMP_PROC_BIND", "close", 1);
    setenv("OMP_PLACES",    "cores", 1);
    omp_set_num_threads(1);

    struct CSRMatrix*   csr  = read_matrix(argv[1]);
    struct Path*        path = split_path(argv[1]);
    struct Permutations* perm = compute_permutations(csr, path->file);
    
    struct CSRMatrix* csr_rcm   = permute_csr(csr, perm->rcm_perm);
    struct CSRMatrix* csr_amd   = permute_csr(csr, perm->amd_perm);
    struct CSRMatrix* csr_nd = permute_csr(csr, perm->nd_perm);

    assert_permutation_correct(csr, csr_rcm, perm->rcm_perm, "RCM");
    assert_permutation_correct(csr, csr_amd, perm->amd_perm, "AMD");
    assert_permutation_correct(csr, csr_nd,  perm->nd_perm, "ND");

    export_permutations(csr, perm);
    
    cleanup(csr, csr_rcm, csr_amd, csr_nd, perm, path);

    return EXIT_SUCCESS;
}

void cleanup(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm, struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd, struct Permutations* perm, struct Path* path) {
    csr_free(csr); csr_free(csr_rcm);
    csr_free(csr_amd); csr_free(csr_nd);
    free(perm->rcm_perm); free(perm->amd_perm); free(perm->nd_perm);
    free(perm);
    free((void*)path->file); free((void*)path->folder);
    free(path);
}

struct Path* split_path(char* arg) {
    struct Path* local_path = malloc(sizeof(struct Path));
    char* copy = strdup(arg);
    
    local_path->folder = strdup(strtok(copy, "/"));
    
    char* file = strtok(NULL, "/");
    char* dot = strrchr(file, '.');
    if (dot) *dot = '\0';
    local_path->file = strdup(file);
    
    free(copy);
    return local_path;
}

void export_permutations(struct CSRMatrix* csr, struct Permutations* perm){
    FILE* rcm_file = fopen("validation/rcm.txt", "w");
    FILE* amd_file = fopen("validation/amd.txt", "w");
    FILE* nd_file = fopen("validation/nd.txt", "w");

    for(int i = 0; i < csr->n; i++){
        fprintf(rcm_file, "%d\n", perm->rcm_perm[i]);
        fprintf(amd_file, "%d\n", perm->amd_perm[i]);
        fprintf(nd_file, "%d\n", perm->nd_perm[i]);
    }
    puts("Permutations are saved successfully!");
    exit(EXIT_SUCCESS);
}

FILE* open_csv(const char* path, const char* header) {
    FILE* f = fopen(path, "r");
    int exists = (f != NULL);
    if (f) fclose(f);
    f = fopen(path, "a");
    if (!f) { perror("fopen"); exit(EXIT_FAILURE); }
    if (!exists)
        fprintf(f, "%s\n", header);
    return f;
}

struct CSRMatrix* read_matrix(char* path){
    struct COOMatrix* coo = coo_parser(path);
    struct CSRMatrix* csr = csr_from_coo(coo);
    coo_free(coo);
    return csr;
}

struct Permutations* compute_permutations(struct CSRMatrix* csr, const char* name){
    FILE* reorder_csv = open_csv("results/reorder_times.csv", "matrix,reordering,time_s");
    struct Permutations* p = malloc(sizeof(struct Permutations));
    double t;
    t = get_time();
    p->rcm_perm = compute_permutation_rcm(csr);
    fprintf(reorder_csv, "%s,rcm,%.4f\n", name, get_time() - t);

    t = get_time();
    p->amd_perm = compute_permutation_amd(csr);
    fprintf(reorder_csv, "%s,amd,%.4f\n", name, get_time() - t);

    t = get_time();
    p->nd_perm = compute_permutation_nd(csr);
    fprintf(reorder_csv, "%s,nd,%.4f\n", name, get_time() - t);

    fclose(reorder_csv);
    return p;
}

void assert_permutation_correct(struct CSRMatrix* original, struct CSRMatrix* reordered, int* p, const char* label) {
    int n = original->n;
    double* x      = malloc(n * sizeof(double));
    double* y_orig  = calloc(n, sizeof(double));
    double* y_reord = calloc(n, sizeof(double));
    double* y_back  = calloc(n, sizeof(double));
    double* px      = malloc(n * sizeof(double));

    for (int i = 0; i < n; i++) x[i] = (double)(i % 7 + 1);

    // y = Ax
    spmv_csr_seq(original, x, y_orig);

    // x' = Px
    for (int i = 0; i < n; i++) px[i] = x[p[i]];

    // y' = A'x'
    spmv_csr_seq(reordered, px, y_reord);

    // y_back[old] = y_reord[new]
    for (int i = 0; i < n; i++) y_back[p[i]] = y_reord[i];

    double max_err = 0.0;
    for (int i = 0; i < n; i++) {
        double err = fabs(y_orig[i] - y_back[i]);
        if (err > max_err) max_err = err;
    }

    if (max_err > 1e-10)
        fprintf(stderr, "CORRECTNESS FAIL [%s]: max_err = %e\n", label, max_err);
    else
        printf("Correctness OK [%s]: max_err = %e\n", label, max_err);
        
    free(x); free(px); free(y_orig); free(y_reord); free(y_back);
}