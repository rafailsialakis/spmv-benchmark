/* Failure controls for the permutation checks.
 *   ok           valid permutation, untouched reordered matrix   -> exit 0
 *   dup          permutation with a duplicate entry               -> exit 1
 *   range        permutation with an out-of-range entry           -> exit 1
 *   corrupt      one value of the reordered matrix changed        -> exit 1
 *   wrong_perm   checked against a different (valid) permutation  -> exit 1
 */
#include <stdio.h>
#include <string.h>
#include "matrix/csr.h"
#include "reorder/reorder.h"
#include "utils/utils.h"

int main(int argc, char** argv) {
    const char* mode = argc > 1 ? argv[1] : "ok";
    // 4x4 symmetric tridiagonal matrix with distinct values
    int    row_ptr[] = {0, 2, 5, 8, 10};
    int    col_idx[] = {0, 1, 0, 1, 2, 1, 2, 3, 2, 3};
    double values[]  = {4, -1, -1, 5, -2, -2, 6, -3, -3, 7};
    struct CSRMatrix a = {4, 10, row_ptr, col_idx, values};

    int p[4]     = {2, 0, 3, 1};
    int other[4] = {1, 3, 0, 2};
    if (strcmp(mode, "dup") == 0)   { p[3] = 0; validate_permutation(p, 4, "dup"); }
    if (strcmp(mode, "range") == 0) { p[3] = 9; validate_permutation(p, 4, "range"); }

    struct CSRMatrix* b = permute_csr(&a, p);
    if (strcmp(mode, "corrupt") == 0) b->values[3] += 1e-6;
    assert_permutation_correct(&a, b, strcmp(mode, "wrong_perm") == 0 ? other : p, mode);
    puts("CHECK PASSED");
    csr_free(b);
    return 0;
}
