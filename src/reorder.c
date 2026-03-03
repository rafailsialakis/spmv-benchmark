#include <stdio.h>
#include "../include/csr.h"
#include "../include/reorder.h"

int* compute_permutation_rcm(struct CSRMatrix* csr) {
    cs* A  = cs_spalloc(csr->n, csr->n, csr->nnz, 1, 0);
    // For symmetric matrices CSC == CSR
    A->p  = csr->row_ptr;   
    A->i  = csr->col_idx;   
    A->x  = csr->values;
    A->nz = -1;

    int* p = cs_symrcm(A);
    cs_spfree(A);
    return p;
}

int* compute_permutation_metis(struct CSRMatrix* csr) {
    idx_t  n    = csr->n;
    idx_t* p    = malloc(n * sizeof(idx_t));
    idx_t* ip   = malloc(n * sizeof(idx_t));

    // Φτιάξε row_ptr και col_idx χωρίς διαγώνια
    idx_t* row_ptr = malloc((n+1) * sizeof(idx_t));
    idx_t* col_idx = malloc(csr->nnz * sizeof(idx_t));

    int nnz_no_diag = 0;
    row_ptr[0] = 0;
    for (int i = 0; i < n; i++) {
        for (int j = csr->row_ptr[i]; j < csr->row_ptr[i+1]; j++) {
            if (csr->col_idx[j] != i) {  // παράλειψε διαγώνιο
                col_idx[nnz_no_diag++] = csr->col_idx[j];
            }
        }
        row_ptr[i+1] = nnz_no_diag;
    }

    METIS_NodeND(&n, row_ptr, col_idx, NULL, NULL, p, ip);

    free(ip);
    free(row_ptr);
    free(col_idx);
    return (int*) p;
}

struct CSRMatrix* permute_csr(struct CSRMatrix* csr, int* p) {
    int n   = csr->n;
    int nnz = csr->nnz;

    // Inverse permutation for rows
    int* inv_p = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++)
        inv_p[p[i]] = i;

    struct CSRMatrix* new_csr = malloc(sizeof(struct CSRMatrix));
    new_csr->n       = n;
    new_csr->nnz     = nnz;
    new_csr->row_ptr = calloc(n + 1, sizeof(int));
    new_csr->col_idx = malloc(nnz * sizeof(int));
    new_csr->values  = malloc(nnz * sizeof(double));

    // Count nnz per new rows
    for (int i = 0; i < n; i++) {
        int old_row = p[i];
        new_csr->row_ptr[i+1] = csr->row_ptr[old_row+1]
                               - csr->row_ptr[old_row];
    }

    // Calculate prefix sum
    for (int i = 1; i <= n; i++)
        new_csr->row_ptr[i] += new_csr->row_ptr[i-1];

    // Fill in col idx and value
    for (int i = 0; i < n; i++) {
        int old_row = p[i];
        int new_pos = new_csr->row_ptr[i];
        for (int j = csr->row_ptr[old_row]; j < csr->row_ptr[old_row+1]; j++) {
            new_csr->col_idx[new_pos] = inv_p[csr->col_idx[j]];
            new_csr->values[new_pos]  = csr->values[j];
            new_pos++;
        }
    }

    free(inv_p);
    return new_csr;
}