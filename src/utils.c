#include "../include/csr.h"
#include "../include/spmv.h"
#include "../include/utils.h"
#include "../include/timer.h"
#include "../include/parser.h"
#include "../include/metrics.h"
#include "../include/reorder.h"
#include "../include/benchmark.h"


void compute_matrix_metrics(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm, struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd, struct Path* path){
    FILE* metrics_csv  = open_csv("results/metrics.csv",  "matrix,category,n,nnz,avg_nnz_row,std_nnz_row,bw,rcm_bw,amd_bw,nd_bw,avg_bw,avg_rcm_bw,avg_amd_bw,avg_nd_bw,lb,rcm_lb,amd_lb,nd_lb,density");
    struct BWResult bw = compute_bandwidth(csr);
    struct BWResult bw_rcm = compute_bandwidth(csr_rcm);
    struct BWResult bw_amd = compute_bandwidth(csr_amd);
    struct BWResult bw_nd = compute_bandwidth(csr_nd);

    double lb = compute_imbalance_ratio(csr,MAX_NUM_THREADS);
    double lb_rcm = compute_imbalance_ratio(csr_rcm,MAX_NUM_THREADS);
    double lb_amd = compute_imbalance_ratio(csr_amd,MAX_NUM_THREADS);
    double lb_nd = compute_imbalance_ratio(csr_nd,MAX_NUM_THREADS);

    double avg_nnz = avg_nnz_row(csr);
    double std_nnz = std_nnz_row(csr);
    double density = compute_density(csr);

    fprintf(metrics_csv,"%s,%s,%d,%d,%.2f,%.2f,%d,%d,%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%e\n",path->file,path->folder,csr->n,csr->nnz,avg_nnz,std_nnz,bw.max_bw,bw_rcm.max_bw,bw_amd.max_bw, bw_nd.max_bw, bw.avg_bw, bw_rcm.avg_bw, bw_amd.avg_bw, bw_nd.avg_bw, lb, lb_rcm, lb_amd, lb_nd, density);    
    fclose(metrics_csv);
}

void run_all_benchmarks(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm, struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd, struct Path* path) {
    double* x = malloc(csr->n * sizeof(double));
    double* y = malloc(csr->n * sizeof(double));
    for (int i = 0; i < csr->n; i++) x[i] = 1.0;

    FILE* rax_csv  = open_csv("results/rax.csv",  "matrix,category,reordering,threads,gflops,time_ms");
    FILE* ios_csv  = open_csv("results/ios.csv",  "matrix,category,reordering,threads,gflops,time_ms");
    FILE* cold_csv = open_csv("results/cold.csv", "matrix,category,reordering,threads,gflops,time_ms");

    struct CSRMatrix* matrices[4] = {csr, csr_rcm, csr_amd, csr_nd};
    const char* reorderings[4]   = {"none", "rcm", "amd", "nd"};
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
            fprintf(rax_csv,  "%s,%s,%s,%d,%.4f,%.3f\n", path->file, path->folder, reorderings[r], threads, rax[r].gflops,  rax[r].time_ms);
            fprintf(ios_csv,  "%s,%s,%s,%d,%.4f,%.3f\n", path->file, path->folder, reorderings[r], threads, ios[r].gflops,  ios[r].time_ms);
            fprintf(cold_csv, "%s,%s,%s,%d,%.4f,%.3f\n", path->file, path->folder, reorderings[r], threads, cold[r].gflops, cold[r].time_ms);
        }
    }

    fclose(rax_csv); fclose(ios_csv); fclose(cold_csv);
    free(x); free(y);
}

void run_cache_benchmarks(struct CSRMatrix* csr, struct CSRMatrix* csr_rcm, struct CSRMatrix* csr_amd, struct CSRMatrix* csr_nd, struct Path* path){
    int EventSet = PAPI_NULL;
    long long values[3];
    int events[3] = {PAPI_L1_DCM, PAPI_L2_DCM, PAPI_L3_TCM};

    if (PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT) {
        printf("PAPI init error\n");
        return;
    }
    PAPI_create_eventset(&EventSet);
    PAPI_add_events(EventSet, events, 3);

    double* x = malloc(csr->n * sizeof(double));
    double* y = malloc(csr->n * sizeof(double));
    for (int i = 0; i < csr->n; i++) x[i] = 1.0;

    FILE* cache_csv = open_csv("results/cache.csv", "matrix,category,reordering,L1_misses,L2_misses,L3_misses");

    struct CSRMatrix* matrices[4]  = {csr, csr_rcm, csr_amd, csr_nd};
    const char* reorderings[4]     = {"none", "rcm", "amd", "nd"};
    
    printf("\n%-8s%-12s%-12s%-12s\n", "Reorder", "L1_misses", "L2_misses", "L3_misses");
    for (int r = 0; r < 4; r++) {
        memset(y, 0, csr->n * sizeof(double));

        PAPI_reset(EventSet);
        PAPI_start(EventSet);
        spmv_csr_seq(matrices[r], x, y);
        PAPI_stop(EventSet, values);

        fprintf(cache_csv, "%s,%s,%s,%lld,%lld,%lld\n",
                path->file, path->folder, reorderings[r],
                values[0], values[1], values[2]);
        printf("%-8s%-12lld%-12lld%-12lld\n",reorderings[r], values[0], values[1], values[2]);                    
    }
    PAPI_cleanup_eventset(EventSet);
    PAPI_destroy_eventset(&EventSet);
    fclose(cache_csv);
    free(x); free(y);
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

    if (max_err > 1e-10){
        fprintf(stderr, "CORRECTNESS FAIL [%s]: max_err = %e\n", label, max_err);
        exit(EXIT_FAILURE);
    }
    free(x); free(px); free(y_orig); free(y_reord); free(y_back);
}