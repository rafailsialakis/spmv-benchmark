#include <math.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include "spmv/spmv.h"
#include "matrix/csr.h"
#include "utils/utils.h"
#include "matrix/parser.h"
#include "benchmark/timer.h"
#include "reorder/reorder.h"
#include "benchmark/metrics.h"
#include "benchmark/benchmark.h"

const char* const REORDERING_NAMES[N_REORDERINGS] = {"none", "rcm", "amd", "nd", "gp"};

static void ensure_results_dir(void) {
    if (mkdir("results", 0755) != 0 && errno != EEXIST) {
        perror("mkdir results");
        exit(EXIT_FAILURE);
    }

    if (mkdir(RESULTS_DIR, 0755) != 0 && errno != EEXIST) {
        perror("mkdir " RESULTS_DIR);
        exit(EXIT_FAILURE);
    }
}

void compute_matrix_metrics(struct MatrixSet* set) {
    struct CSRMatrix *csr = set->m[0], *csr_rcm = set->m[1], *csr_amd = set->m[2],
                     *csr_nd = set->m[3], *csr_gp = set->m[4];
    struct Path* path = set->path;
    FILE* metrics_csv = open_csv(
        RESULTS_DIR "/metrics.csv",
        "matrix,category,n,nnz,avg_nnz_row,std_nnz_row,"
        "bw,rcm_bw,amd_bw,nd_bw,gp_bw,"
        "avg_bw,avg_rcm_bw,avg_amd_bw,avg_nd_bw,avg_gp_bw,"
        "lb,rcm_lb,amd_lb,nd_lb,gp_lb,density"
    );

    struct BWResult bw     = compute_bandwidth(csr);
    struct BWResult bw_rcm = compute_bandwidth(csr_rcm);
    struct BWResult bw_amd = compute_bandwidth(csr_amd);
    struct BWResult bw_nd  = compute_bandwidth(csr_nd);
    struct BWResult bw_gp  = compute_bandwidth(csr_gp);

    double lb     = compute_imbalance_ratio(csr,     MAX_NUM_THREADS);
    double lb_rcm = compute_imbalance_ratio(csr_rcm, MAX_NUM_THREADS);
    double lb_amd = compute_imbalance_ratio(csr_amd, MAX_NUM_THREADS);
    double lb_nd  = compute_imbalance_ratio(csr_nd,  MAX_NUM_THREADS);
    double lb_gp  = compute_imbalance_ratio(csr_gp,  MAX_NUM_THREADS);

    double avg_nnz = avg_nnz_row(csr);
    double std_nnz = std_nnz_row(csr);
    double density = compute_density(csr);

    fprintf(metrics_csv,
        "%s,%s,%d,%d,%.2f,%.2f,"
        "%d,%d,%d,%d,%d,"
        "%.2f,%.2f,%.2f,%.2f,%.2f,"
        "%.2f,%.2f,%.2f,%.2f,%.2f,%e\n",
        path->file, path->folder, csr->n, csr->nnz, avg_nnz, std_nnz,
        bw.max_bw, bw_rcm.max_bw, bw_amd.max_bw, bw_nd.max_bw, bw_gp.max_bw,
        bw.avg_bw, bw_rcm.avg_bw, bw_amd.avg_bw, bw_nd.avg_bw, bw_gp.avg_bw,
        lb, lb_rcm, lb_amd, lb_nd, lb_gp, density
    );
    fclose(metrics_csv);
}

static int env_int(const char* name, int fallback) {
    const char* v = getenv(name);
    if (!v || !*v) return fallback;
    char* end;
    long x = strtol(v, &end, 10);
    if (*end != '\0' || x <= 0 || x > 1000000) {
        fprintf(stderr, "Invalid %s=%s\n", name, v);
        exit(EXIT_FAILURE);
    }
    return (int)x;
}

// Any non-negative 64-bit seed (no upper bound, unlike env_int).
static uint64_t env_seed(const char* name, uint64_t fallback) {
    const char* v = getenv(name);
    if (!v || !*v) return fallback;
    char* end;
    errno = 0;
    unsigned long long x = strtoull(v, &end, 10);
    if (*end != '\0' || errno == ERANGE || v[0] == '-') {
        fprintf(stderr, "Invalid %s=%s\n", name, v);
        exit(EXIT_FAILURE);
    }
    return (uint64_t)x;
}

// Small self-contained PRNG (splitmix64), so the shuffles are identical on
// x86 and ARM and do not depend on the libc rand() implementation.
static uint64_t splitmix64(uint64_t* state) {
    uint64_t z = (*state += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static uint64_t fnv1a(const char* str) {
    uint64_t h = 1469598103934665603ULL;
    for (; *str; str++) { h ^= (unsigned char)*str; h *= 1099511628211ULL; }
    return h;
}

static void shuffle(int* a, int n, uint64_t* state) {
    for (int k = n - 1; k > 0; k--) {                      // Fisher-Yates
        int j = (int)(splitmix64(state) % (uint64_t)(k + 1));
        int t = a[k]; a[k] = a[j]; a[j] = t;
    }
}

void run_all_benchmarks(struct MatrixSet* set) {
    struct CSRMatrix* csr = set->m[0];
    struct Path* path = set->path;
    double* x = malloc(csr->n * sizeof(double));
    double* y = malloc(csr->n * sizeof(double));
    for (int i = 0; i < csr->n; i++) x[i] = 1.0;

    FILE* rax_csv  = open_csv(RESULTS_DIR "/rax.csv",  "matrix,category,reordering,threads,gflops,time_ms,rep,pos");
    FILE* ios_csv  = open_csv(RESULTS_DIR "/ios.csv",  "matrix,category,reordering,threads,gflops,time_ms,rep,pos,nonnormal");
    FILE* cold_csv = open_csv(RESULTS_DIR "/cold.csv", "matrix,category,reordering,threads,gflops,time_ms,rep,pos");

    int thread_counts[3] = {1, 2, 4};
    int reps = env_int("SPMV_REPS", N_REPS);
    uint64_t state = env_seed("SPMV_SEED", DEFAULT_SHUFFLE_SEED) ^ fnv1a(path->file);
    printf("\nRepetitions: %d\n", reps);

    for (int rep = 0; rep < reps; rep++) {
        for (int ti = 0; ti < 3; ti++) {
            int threads = thread_counts[ti];
            omp_set_num_threads(threads);

            int order[N_REORDERINGS];
            for (int k = 0; k < N_REORDERINGS; k++) order[k] = k;
            shuffle(order, N_REORDERINGS, &state);

            printf("\nRep: %d  Threads: %d\n", rep, threads);
            printf("%s\t%s\t%s\t%s\n", "Method", "Reorder", "T(ms)", "GFLOP/s");

            for (int pos = 0; pos < N_REORDERINGS; pos++) {
                int r = order[pos];
                const char* name = REORDERING_NAMES[r];
                BenchResult rax  = run_benchmark_rax( name, set->m[r], x, y);
                BenchResult ios  = run_benchmark_ios( name, set->m[r], x, y);
                BenchResult cold = run_benchmark_cold(name, set->m[r], x, y);

                fprintf(rax_csv,  "%s,%s,%s,%d,%.6f,%.6f,%d,%d\n",    path->file, path->folder, name, threads, rax.gflops,  rax.time_ms,  rep, pos);
                fprintf(ios_csv,  "%s,%s,%s,%d,%.6f,%.6f,%d,%d,%d\n", path->file, path->folder, name, threads, ios.gflops,  ios.time_ms,  rep, pos, ios.nonnormal);
                fprintf(cold_csv, "%s,%s,%s,%d,%.6f,%.6f,%d,%d\n",    path->file, path->folder, name, threads, cold.gflops, cold.time_ms, rep, pos);
            }
        }
        fflush(rax_csv); fflush(ios_csv); fflush(cold_csv);
    }

    fclose(rax_csv); fclose(ios_csv); fclose(cold_csv);
    free(x); free(y);
}

void ios_numeric_scan(struct MatrixSet* set) {
    struct CSRMatrix* csr = set->m[0];
    double* in  = malloc(csr->n * sizeof(double));
    double* out = malloc(csr->n * sizeof(double));
    for (int i = 0; i < csr->n; i++) in[i] = 1.0;

    int first = -1, affected = 0, worst = 0;
    for (int it = 0; it < N_RUNS; it++) {
        spmv_csr(csr, in, out);
        int bad = count_nonnormal(out, csr->n);
        if (bad > 0) {
            if (first < 0) first = it;
            affected++;
            if (bad > worst) worst = bad;
        }
        double* tmp = in; in = out; out = tmp;
    }
    if (affected > 0)
        fprintf(stderr, "WARNING IOS scan [%s]: %d of %d iterations produced subnormal/inf/NaN "
                        "values (first at iteration %d, up to %d entries)\n",
                set->path->file, affected, N_RUNS, first, worst);

    FILE* csv = open_csv(RESULTS_DIR "/ios_scan.csv",
                         "matrix,category,iters,first_nonnormal_iter,iters_with_nonnormal,max_nonnormal");
    fprintf(csv, "%s,%s,%d,%d,%d,%d\n", set->path->file, set->path->folder,
            N_RUNS, first, affected, worst);
    fclose(csv);
    free(in); free(out);
}

void run_cache_benchmarks(struct MatrixSet* set) {
    struct CSRMatrix* csr = set->m[0];
    struct Path* path = set->path;
    int EventSet = PAPI_NULL;
    #if defined(__aarch64__)
        #define NUM_CACHE_EVENTS 2
        int events[NUM_CACHE_EVENTS] = {PAPI_L1_DCM, PAPI_L2_DCM};
        const char* cache_header = "matrix,category,reordering,L1_misses,L2_misses";
    #elif defined(__x86_64__)
        #define NUM_CACHE_EVENTS 3
        int events[NUM_CACHE_EVENTS] = {PAPI_L1_DCM, PAPI_L2_DCM, PAPI_L3_TCM};
        const char* cache_header = "matrix,category,reordering,L1_misses,L2_misses,L3_misses";
    #endif

    long long values[NUM_CACHE_EVENTS];

    if (PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT) {
        printf("PAPI init error\n");
        return;
    }
    PAPI_create_eventset(&EventSet);
    PAPI_add_events(EventSet, events, NUM_CACHE_EVENTS);

    double* x = malloc(csr->n * sizeof(double));
    double* y = malloc(csr->n * sizeof(double));
    for (int i = 0; i < csr->n; i++) x[i] = 1.0;

    FILE* cache_csv = open_csv(RESULTS_DIR "/cache.csv", cache_header);

    struct CSRMatrix** matrices = set->m;
    const char* const* reorderings = REORDERING_NAMES;

    #if defined(__aarch64__)
        printf("\n%-8s%-12s%-12s\n", "Reorder", "L1_misses", "L2_misses");
    #else
        printf("\n%-8s%-12s%-12s%-12s\n", "Reorder", "L1_misses", "L2_misses", "L3_misses");
    #endif

    for (int r = 0; r < N_REORDERINGS; r++) {
        memset(y, 0, csr->n * sizeof(double));
        PAPI_reset(EventSet);
        PAPI_start(EventSet);
        spmv_csr(matrices[r], x, y);
        PAPI_stop(EventSet, values);
        #if defined(__aarch64__)
            fprintf(cache_csv, "%s,%s,%s,%lld,%lld\n",
                    path->file, path->folder, reorderings[r],
                    values[0], values[1]);
            printf("%-8s%-12lld%-12lld\n", reorderings[r], values[0], values[1]);
        #else
            fprintf(cache_csv, "%s,%s,%s,%lld,%lld,%lld\n",
                    path->file, path->folder, reorderings[r],
                    values[0], values[1], values[2]);
            printf("%-8s%-12lld%-12lld%-12lld\n", reorderings[r], values[0], values[1], values[2]);
        #endif
    }
    PAPI_cleanup_eventset(EventSet);
    PAPI_destroy_eventset(&EventSet);
    fclose(cache_csv);
    free(x); free(y);
}

void run_tlb_benchmarks(struct MatrixSet* set) {
    struct CSRMatrix* csr = set->m[0];
    struct Path* path = set->path;

    if (PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT) {
        fprintf(stderr, "PAPI init error (TLB)\n");
        return;
    }

    int EventSet = PAPI_NULL;
    PAPI_create_eventset(&EventSet);

    int ev_dtlb_misses, ev_itlb_misses;
    if (PAPI_event_name_to_code("perf::DTLB-LOAD-MISSES", &ev_dtlb_misses) != PAPI_OK ||
        PAPI_event_name_to_code("perf::ITLB-LOAD-MISSES", &ev_itlb_misses) != PAPI_OK) {
        fprintf(stderr, "TLB events not resolvable on this machine — skipping.\n");
        PAPI_destroy_eventset(&EventSet);
        return;
    }

    int tlb_events[2] = {ev_dtlb_misses, ev_itlb_misses};
    if (PAPI_add_events(EventSet, tlb_events, 2) != PAPI_OK) {
        fprintf(stderr, "Cannot add TLB events to EventSet — skipping.\n");
        PAPI_destroy_eventset(&EventSet);
        return;
    }

    double* x = malloc(csr->n * sizeof(double));
    double* y = malloc(csr->n * sizeof(double));
    for (int i = 0; i < csr->n; i++) x[i] = 1.0;

    FILE* tlb_csv = open_csv(
        RESULTS_DIR "/tlb.csv",
        "matrix,category,reordering,dtlb_load_misses,itlb_load_misses"
    );

    struct CSRMatrix**       matrices    = set->m;
    const char* const*       reorderings = REORDERING_NAMES;

    printf("\n%-8s  %-20s  %-20s\n",
           "Reorder", "DTLB-load-misses", "ITLB-load-misses");

    long long values[2];

    for (int r = 0; r < N_REORDERINGS; r++) {
        memset(y, 0, csr->n * sizeof(double));

        PAPI_reset(EventSet);
        PAPI_start(EventSet);
        spmv_csr(matrices[r], x, y);
        PAPI_stop(EventSet, values);

        fprintf(tlb_csv, "%s,%s,%s,%lld,%lld\n",
                path->file, path->folder, reorderings[r],
                values[0], values[1]);

        printf("%-8s  %-20lld  %-20lld\n",
               reorderings[r], values[0], values[1]);
    }

    PAPI_cleanup_eventset(EventSet);
    PAPI_destroy_eventset(&EventSet);
    fclose(tlb_csv);
    free(x); free(y);
}

void free_matrix_set(struct MatrixSet* set) {
    for (int r = 0; r < N_REORDERINGS; r++) csr_free(set->m[r]);
    free(set->perm->rcm_perm); free(set->perm->amd_perm);
    free(set->perm->nd_perm);  free(set->perm->gp_perm);
    free(set->perm);
    free((void*)set->path->file); free((void*)set->path->folder);
    free(set->path);
    free(set);
}

struct Path* split_path(char* arg) {
    struct Path* local_path = malloc(sizeof(struct Path));
    char* copy = strdup(arg);

    local_path->folder = strdup(strtok(copy, "/"));

    char* file = strtok(NULL, "/");
    char* dot  = strrchr(file, '.');
    if (dot) *dot = '\0';
    local_path->file = strdup(file);

    free(copy);
    return local_path;
}

void export_permutations(struct MatrixSet* set) {
    struct CSRMatrix* csr = set->m[0];
    struct Permutations* perm = set->perm;
    FILE* rcm_file = fopen("validation/rcm.txt", "w");
    FILE* amd_file = fopen("validation/amd.txt", "w");
    FILE* nd_file  = fopen("validation/nd.txt",  "w");
    FILE* gp_file  = fopen("validation/gp.txt",  "w");

    for (int i = 0; i < csr->n; i++) {
        fprintf(rcm_file, "%d\n", perm->rcm_perm[i]);
        fprintf(amd_file, "%d\n", perm->amd_perm[i]);
        fprintf(nd_file,  "%d\n", perm->nd_perm[i]);
        fprintf(gp_file,  "%d\n", perm->gp_perm[i]);
    }
    puts("Permutations saved successfully!");
    exit(EXIT_SUCCESS);
}

FILE* open_csv(const char* path, const char* header) {
    ensure_results_dir();

    FILE* f = fopen(path, "r");
    int exists = (f != NULL);
    if (f) {
        char first[1024] = {0};
        if (fgets(first, sizeof(first), f) != NULL) {
            first[strcspn(first, "\r\n")] = '\0';
            if (strcmp(first, header) != 0) {
                fprintf(stderr,
                        "ERROR: %s exists with a different header.\n"
                        "  found:    %s\n  expected: %s\n"
                        "Move the old results away before running (e.g. mv %s %s.old).\n",
                        path, first, header, path, path);
                exit(EXIT_FAILURE);
            }
        } else {
            exists = 0;   // empty file: write the header
        }
        fclose(f);
    }
    f = fopen(path, "a");
    if (!f) { perror("fopen"); exit(EXIT_FAILURE); }
    if (!exists)
        fprintf(f, "%s\n", header);
    return f;
}

struct CSRMatrix* read_matrix(char* path) {
    struct COOMatrix* coo = coo_parser(path);
    struct CSRMatrix* csr = csr_from_coo(coo);
    coo_free(coo);
    return csr;
}

struct Permutations* compute_permutations(struct CSRMatrix* csr) {
    struct Permutations* p = malloc(sizeof(struct Permutations));
    double t;

    t = get_time();
    p->rcm_perm = compute_permutation_rcm(csr);
    p->order_s[0] = get_time() - t;

    t = get_time();
    p->amd_perm = compute_permutation_amd(csr);
    p->order_s[1] = get_time() - t;

    t = get_time();
    p->nd_perm = compute_permutation_nd(csr);
    p->order_s[2] = get_time() - t;

    t = get_time();
    p->gp_perm = compute_permutation_gp(csr);
    p->order_s[3] = get_time() - t;

    validate_permutation(p->rcm_perm, csr->n, "RCM");
    validate_permutation(p->amd_perm, csr->n, "AMD");
    validate_permutation(p->nd_perm,  csr->n, "ND");
    validate_permutation(p->gp_perm,  csr->n, "GP");
    return p;
}

void require_symmetric_pattern(const struct CSRMatrix* sorted, const char* name) {
    long long dup  = csr_duplicate_entries(sorted);
    long long asym = csr_pattern_asymmetry(sorted);
    if (dup > 0 || asym > 0) {
        fprintf(stderr,
                "ERROR [%s]: the sparsity pattern is not usable for symmetric orderings:\n"
                "  duplicate entries: %lld\n"
                "  off-diagonal entries without a transpose partner: %lld of %d nonzeros\n"
                "RCM, AMD and Scotch treat the pattern as an undirected graph (Scotch ND does not\n"
                "terminate on an unsymmetric one). Drop the matrix or order A+A^T explicitly.\n",
                name, dup, asym, sorted->nnz);
        exit(EXIT_FAILURE);
    }
    printf("Pattern: structurally symmetric, no duplicate entries\n");
}

struct MatrixSet* prepare_matrices(char* arg, int save_times) {
    struct MatrixSet* set = calloc(1, sizeof(struct MatrixSet));
    set->path = split_path(arg);

    struct CSRMatrix* original = read_matrix(arg);

    // Baseline: the original ordering, rebuilt by the same routine as the others
    // (sorted columns), and checked before any ordering algorithm sees the graph.
    int* id = identity_permutation(original->n);
    set->m[0] = permute_csr(original, id);
    assert_permutation_correct(original, set->m[0], id, "none");
    free(id);
    require_symmetric_pattern(set->m[0], set->path->file);

    // Orderings are computed on the parsed matrix, exactly as before the refactor.
    set->perm = compute_permutations(original);
    csr_free(original);   // keeps peak memory at five matrices

    int* perms[N_METHODS] = {set->perm->rcm_perm, set->perm->amd_perm,
                             set->perm->nd_perm,  set->perm->gp_perm};
    for (int k = 0; k < N_METHODS; k++) {
        double t = get_time();
        set->m[k + 1] = permute_csr(set->m[0], perms[k]);
        set->apply_s[k] = get_time() - t;
        assert_permutation_correct(set->m[0], set->m[k + 1], perms[k], REORDERING_NAMES[k + 1]);
    }
    fprintf(stdout, "%s\n", "All tests passed!");

    if (save_times) {
        FILE* csv = open_csv(RESULTS_DIR "/reorder_times.csv", "matrix,reordering,order_s,apply_s");
        for (int k = 0; k < N_METHODS; k++)
            fprintf(csv, "%s,%s,%.6f,%.6f\n", set->path->file, REORDERING_NAMES[k + 1],
                    set->perm->order_s[k], set->apply_s[k]);
        fclose(csv);
    }
    return set;
}

void assert_permutation_correct(struct CSRMatrix* original, struct CSRMatrix* reordered,
                                int* p, const char* label) {
    int n = original->n;
    validate_permutation(p, n, label);
    if (reordered->n != n || reordered->nnz != original->nnz) {
        fprintf(stderr, "CORRECTNESS FAIL [%s]: size mismatch after permutation\n", label);
        exit(EXIT_FAILURE);
    }
    double* x       = malloc(n * sizeof(double));
    double* y_orig  = calloc(n, sizeof(double));
    double* y_reord = calloc(n, sizeof(double));
    double* y_back  = calloc(n, sizeof(double));
    double* px      = malloc(n * sizeof(double));

    for (int i = 0; i < n; i++) x[i] = (double)(i % 7 + 1);

    spmv_csr(original, x, y_orig);              // y = Ax
    for (int i = 0; i < n; i++) px[i] = x[p[i]];   // x' = Px
    spmv_csr(reordered, px, y_reord);            // y' = A'x'
    for (int i = 0; i < n; i++) y_back[p[i]] = y_reord[i]; // y_back = P^T y'

    // Reordering changes the summation order, so rounding differences scale with
    // the magnitude of the row terms: compare against sum_j |a_ij * x_j| per row.
    double max_err = 0.0;
    for (int i = 0; i < n; i++) {
        double scale = 0.0;
        for (int k = original->row_ptr[i]; k < original->row_ptr[i + 1]; k++)
            scale += fabs(original->values[k] * x[original->col_idx[k]]);
        double err = fabs(y_orig[i] - y_back[i]) / (scale > 0.0 ? scale : 1.0);
        if (err > max_err) max_err = err;
    }

    if (max_err > 1e-12) {
        fprintf(stderr, "CORRECTNESS FAIL [%s]: max_rel_err = %e\n", label, max_err);
        exit(EXIT_FAILURE);
    }
    free(x); free(px); free(y_orig); free(y_reord); free(y_back);
}
