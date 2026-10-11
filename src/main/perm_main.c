#include "spmv/spmv.h"
#include "matrix/csr.h"
#include "utils/utils.h"
#include "matrix/parser.h"
#include "benchmark/timer.h"
#include "reorder/reorder.h"
#include "benchmark/metrics.h"
#include "benchmark/benchmark.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <file.mtx>\n", argv[0]);
        return EXIT_FAILURE;
    }
    omp_set_num_threads(1);

    struct CSRMatrix*   csr  = read_matrix(argv[1]);
    struct Path*        path = split_path(argv[1]);
    struct Permutations* perm = compute_permutations(csr, path->file, 0);
    
    struct CSRMatrix* csr_rcm   = permute_csr(csr, perm->rcm_perm);
    struct CSRMatrix* csr_amd   = permute_csr(csr, perm->amd_perm);
    struct CSRMatrix* csr_nd    = permute_csr(csr, perm->nd_perm);
    struct CSRMatrix* csr_gp    = permute_csr(csr, perm->gp_perm);

    assert_permutation_correct(csr, csr_rcm, perm->rcm_perm, "RCM");
    assert_permutation_correct(csr, csr_amd, perm->amd_perm, "AMD");
    assert_permutation_correct(csr, csr_nd,  perm->nd_perm, "ND");
    assert_permutation_correct(csr, csr_gp,  perm->gp_perm, "GP");
    fprintf(stdout, "%s\n", "All tests passed!");

    export_permutations(csr, perm);
    
    cleanup(csr, csr_rcm, csr_amd, csr_nd, csr_gp, perm, path);

    return EXIT_SUCCESS;
}