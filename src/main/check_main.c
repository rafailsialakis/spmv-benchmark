/* Pre-flight check of one matrix: parses it and verifies that the pattern is
 * structurally symmetric with no duplicate entries. Exit status 0 = usable.
 * Run over every matrix with `make check-matrices` before a campaign. */
#include "matrix/csr.h"
#include "utils/utils.h"
#include "reorder/reorder.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <category/file.mtx>\n", argv[0]);
        return EXIT_FAILURE;
    }
    struct CSRMatrix* a = read_matrix(argv[1]);
    int* id = identity_permutation(a->n);
    struct CSRMatrix* sorted = permute_csr(a, id);
    require_symmetric_pattern(sorted, argv[1]);
    printf("OK %s\n", argv[1]);
    free(id); csr_free(sorted); csr_free(a);
    return EXIT_SUCCESS;
}
