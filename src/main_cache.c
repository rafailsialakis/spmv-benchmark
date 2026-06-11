#include "../include/csr.h"
#include "../include/spmv.h"
#include "../include/utils.h"
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
    struct Permutations* perm = compute_permutations(csr, path->file, 0);
    
    struct CSRMatrix* csr_rcm   = permute_csr(csr, perm->rcm_perm);
    struct CSRMatrix* csr_amd   = permute_csr(csr, perm->amd_perm);
    struct CSRMatrix* csr_nd = permute_csr(csr, perm->nd_perm);
    
    assert_permutation_correct(csr, csr_rcm, perm->rcm_perm, "RCM");
    assert_permutation_correct(csr, csr_amd, perm->amd_perm, "AMD");
    assert_permutation_correct(csr, csr_nd,  perm->nd_perm, "ND");
    fprintf(stdout, "%s\n", "All tests passed!");

    run_cache_benchmarks(csr, csr_rcm, csr_amd, csr_nd, path);
    
    cleanup(csr, csr_rcm, csr_amd, csr_nd, perm, path);

    return EXIT_SUCCESS;
}