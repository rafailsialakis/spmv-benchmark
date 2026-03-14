#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/parser.h"
#include "../include/csr.h"
#include "../include/spmv.h"
#include "../include/main.h"
#include "../include/timer.h"
#include "../include/metrics.h"
#include "../include/benchmark.h"
#include "../include/reorder.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <file.mtx>\n", argv[0]);
        return EXIT_FAILURE;
    }

    setenv("OMP_PROC_BIND", "close", 1);
    setenv("OMP_PLACES",    "cores", 1);

    struct CSRMatrix*   csr  = read_matrix(argv[1]);
    struct Path*        path = split_path(argv[1]);
    struct Permutations* perm = compute_permutations(csr, path->file);

    struct CSRMatrix* csr_rcm   = permute_csr(csr, perm->rcm_perm);
    struct CSRMatrix* csr_amd   = permute_csr(csr, perm->amd_perm);
    struct CSRMatrix* csr_metis = permute_csr(csr, perm->metis_perm);

    run_all_benchmarks(csr, csr_rcm, csr_amd, csr_metis, path);
    compute_matrix_metrics(csr, csr_rcm, csr_amd, csr_metis, path);
    cleanup(csr, csr_rcm, csr_amd, csr_metis, perm, path);

    return EXIT_SUCCESS;
}

void compute_matrix_metrics(struct CSRMatrix* csr,
                        struct CSRMatrix* csr_rcm,
                        struct CSRMatrix* csr_amd,
                        struct CSRMatrix* csr_metis,
                        struct Path* path){
    FILE* metrics_csv  = open_csv("results/metrics.csv",  "matrix,category,bw,rcm_bw,amd_bw,metis_bw,lb,rcm_lb,amd_lb,metis_lb,density");
    int bw = compute_bandwidth(csr);
    int bw_rcm = compute_bandwidth(csr_rcm);
    int bw_amd = compute_bandwidth(csr_amd);
    int bw_metis = compute_bandwidth(csr_metis);

    double lb = compute_imbalance_ratio(csr,MAX_NUM_THREADS);
    double lb_rcm = compute_imbalance_ratio(csr_rcm,MAX_NUM_THREADS);
    double lb_amd = compute_imbalance_ratio(csr_amd,MAX_NUM_THREADS);
    double lb_metis = compute_imbalance_ratio(csr_metis,MAX_NUM_THREADS);

    double density = compute_density(csr);

    fprintf(metrics_csv, "%s,%s,%d,%d,%d,%d,%.2f,%.2f,%.2f,%.2f,%e\n", path->file, path->folder, bw, bw_rcm, bw_amd, bw_metis, lb, lb_rcm, lb_amd, lb_metis, density);
    fclose(metrics_csv);
}

void run_all_benchmarks(struct CSRMatrix* csr,
                        struct CSRMatrix* csr_rcm,
                        struct CSRMatrix* csr_amd,
                        struct CSRMatrix* csr_metis,
                        struct Path* path) {

    double* x = malloc(csr->n * sizeof(double));
    double* y = malloc(csr->n * sizeof(double));
    for (int i = 0; i < csr->n; i++) x[i] = 1.0;

    FILE* rax_csv  = open_csv("results/rax.csv",  "matrix,reordering,threads,gflops,time_ms");
    FILE* ios_csv  = open_csv("results/ios.csv",  "matrix,reordering,threads,gflops,time_ms");
    FILE* cold_csv = open_csv("results/cold.csv", "matrix,reordering,threads,gflops,time_ms");

    struct CSRMatrix* matrices[4] = {csr, csr_rcm, csr_amd, csr_metis};
    const char* reorderings[4]   = {"none", "rcm", "amd", "metis"};
    int thread_counts[3]         = {1, 2, 4};

    for (int ti = 0; ti < 3; ti++) {
        int threads = thread_counts[ti];
        omp_set_num_threads(threads);
        BenchResult rax[4], ios[4], cold[4];
        
        printf("\nThreads: %d\n", threads);
        printf("%s\t%s\t%s\t%s\n","Method", "Reorder", "T(ms)", "GFLOP/s");
        for (int r = 0; r < 4; r++) {
            rax[r]  = run_benchmark_rax( reorderings[r], matrices[r], x, y);
            ios[r]  = run_benchmark_ios( reorderings[r], matrices[r], x, y);
            cold[r] = run_benchmark_cold(reorderings[r], matrices[r], x, y);
        }

        for (int r = 0; r < 4; r++) {
            fprintf(rax_csv,  "%s,%s,%d,%.4f,%.3f\n", path->file, reorderings[r], threads, rax[r].gflops,  rax[r].time_ms);
            fprintf(ios_csv,  "%s,%s,%d,%.4f,%.3f\n", path->file, reorderings[r], threads, ios[r].gflops,  ios[r].time_ms);
            fprintf(cold_csv, "%s,%s,%d,%.4f,%.3f\n", path->file, reorderings[r], threads, cold[r].gflops, cold[r].time_ms);
        }
    }

    fclose(rax_csv); fclose(ios_csv); fclose(cold_csv);
    free(x); free(y);
}

void cleanup(struct CSRMatrix* csr,
             struct CSRMatrix* csr_rcm,
             struct CSRMatrix* csr_amd,
             struct CSRMatrix* csr_metis,
             struct Permutations* perm,
             struct Path* path) {
    csr_free(csr); csr_free(csr_rcm);
    csr_free(csr_amd); csr_free(csr_metis);
    free(perm->rcm_perm); free(perm->amd_perm); free(perm->metis_perm);
    free(perm);
    free((void*)path->file); free((void*)path->folder);
    free(path);
}


struct Path* split_path(char* arg) {
    struct Path* local_path = malloc(sizeof(struct Path));
    char* copy = strdup(arg);
    local_path->folder = strdup(strtok(copy, "/"));
    local_path->file   = strdup(strtok(NULL, "/"));
    free(copy);
    return local_path;
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
    p->metis_perm = compute_permutation_metis(csr);
    fprintf(reorder_csv, "%s,metis,%.4f\n", name, get_time() - t);

    fclose(reorder_csv);
    return p;
}