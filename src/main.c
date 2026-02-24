#include <stdio.h>
#include <stdlib.h>
#include "../include/parser.h"
#include "../include/csr.h"
#include "../include/spmv.h"
#include "../include/timer.h"

int main(int argc, char* argv[]) {
    if (argc != 2) {
        printf("Usage: %s <file.mtx>\n", argv[0]);
        return EXIT_FAILURE;
    }

    struct COOMatrix* coo = coo_parser(argv[1]);
    struct CSRMatrix* csr = csr_from_coo(coo);
    coo_free(coo);

    double* x = malloc(csr->n * sizeof(double));
    double* y = malloc(csr->n * sizeof(double));
    for (int i = 0; i < csr->n; i++)
        x[i] = 1.0;

    double start = get_time();
    spmv_csr(csr, x, y);
    double end = get_time();

    printf("Time: %.3f ms\n", (end - start) * 1000.0);

    free(x);
    free(y);
    csr_free(csr);

    return EXIT_SUCCESS;
}