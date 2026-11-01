/* Prints the matrix as the benchmark sees it (parsed, columns sorted):
 * first line "n nnz", then one "row col value" line per stored entry. */
#include <stdio.h>
#include "matrix/csr.h"
#include "utils/utils.h"
#include "reorder/reorder.h"

int main(int argc, char** argv) {
    if (argc < 2) return 2;
    struct CSRMatrix* a = read_matrix(argv[1]);
    int* id = identity_permutation(a->n);
    struct CSRMatrix* s = permute_csr(a, id);
    printf("BEGIN\n%d %d\n", s->n, s->nnz);   // the parser prints its own info lines first
    for (int i = 0; i < s->n; i++)
        for (int k = s->row_ptr[i]; k < s->row_ptr[i + 1]; k++)
            printf("%d %d %.17g\n", i, s->col_idx[k], s->values[k]);
    return 0;
}
