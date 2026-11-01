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
        printf("Usage: %s <category/file.mtx>\n", argv[0]);
        return EXIT_FAILURE;
    }
    struct MatrixSet* set = prepare_matrices(argv[1], 1);

    run_all_benchmarks(set);
    ios_numeric_scan(set);
    compute_matrix_metrics(set);
    free_matrix_set(set);

    return EXIT_SUCCESS;
}
