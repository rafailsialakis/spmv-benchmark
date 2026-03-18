#include "../include/csr.h"
#include "../include/queue.h"
#include "../include/reorder.h"

struct GraphNode* g_nodes; 

int comp(const void *a, const void *b) {
    int na = *(int*) a;
    int nb = *(int*) b;
    return g_nodes[na].degree - g_nodes[nb].degree;
}

int find_start_node(struct GraphNode* nodes, int n){
    int start = 0;
    int min_degree = INT_MAX;
    for(int i = 0; i < n; i++){
        if(nodes[i].degree < min_degree){
            min_degree = nodes[i].degree;
            start = i;
        }
    }
    return start;
}

int* compute_permutation_rcm(struct CSRMatrix* csr){
    struct GraphNode* nodes = malloc(sizeof(struct GraphNode) * csr->n);
    for(int i = 0; i < csr->n; i++){
        nodes[i].id = i;
        nodes[i].degree = 0;
        nodes[i].neighbours = NULL;
        for(int j = csr->row_ptr[i]; j < csr->row_ptr[i+1]; j++){
            if(i != csr->col_idx[j]){
                nodes[i].neighbours = realloc(nodes[i].neighbours, sizeof(int) * (nodes[i].degree + 1));
                nodes[i].neighbours[nodes[i].degree] = csr->col_idx[j];
                nodes[i].degree++;
            }
        }
    }
    struct Queue q;
    q.data = malloc(sizeof(int) * csr->n);
    q.head = 0;
    q.tail = 0;
    g_nodes = nodes;
    bool* visited = calloc(csr->n, sizeof(bool));
    int* perm = malloc(sizeof(int) * csr->n);
    int* rev_perm = malloc(sizeof(int) * csr->n);
    int perm_idx = 0;
    int start = find_start_node(nodes, csr->n);
    enqueue(&q, start);
    visited[start] = true;
    do {
        while(!is_empty(&q)){
            int element = dequeue(&q);
            perm[perm_idx++] = element;
            qsort(nodes[element].neighbours, nodes[element].degree, sizeof(int), comp);
            for(int i = 0; i < nodes[element].degree; i++){
                int neighbour = nodes[element].neighbours[i];
                if(!visited[neighbour]){
                    visited[neighbour] = true;
                    enqueue(&q, neighbour);
                }
            }
        }
        for(int i = 0; i < csr->n; i++){
            if(!visited[i]){
                visited[i] = true;
                enqueue(&q, i);
                break;
            }
        }
    } while(!is_empty(&q));
    for(int i = 0; i < csr->n; i++)
        rev_perm[i] = perm[csr->n - 1 - i];
    free(q.data);
    free(perm);
    free(visited);
    for(int i = 0; i < csr->n; i++) free(nodes[i].neighbours);
    free(nodes);
    return rev_perm;
}

int* compute_permutation_amd(struct CSRMatrix* csr) {
    cs* A  = cs_spalloc(csr->n, csr->n, csr->nnz, 1, 0);
    // For symmetric matrices CSC == CSR
    A->p  = csr->row_ptr;   
    A->i  = csr->col_idx;   
    A->x  = csr->values;
    A->nz = -1;

    int* p = cs_amd(1,A);
    // In order to avoid corrupting memory
    A->p = NULL;
    A->i = NULL;
    A->x = NULL;

    cs_spfree(A);
    
    return p;
}

int* compute_permutation_metis(struct CSRMatrix* csr) {
    idx_t  n    = csr->n;
    idx_t* p    = malloc(n * sizeof(idx_t));
    idx_t* ip   = malloc(n * sizeof(idx_t));

    idx_t* row_ptr = malloc((n+1) * sizeof(idx_t));
    idx_t* col_idx = malloc(csr->nnz * sizeof(idx_t));

    int nnz_no_diag = 0;
    row_ptr[0] = 0;
    for (int i = 0; i < n; i++) {
        for (int j = csr->row_ptr[i]; j < csr->row_ptr[i+1]; j++) {
            if (csr->col_idx[j] != i) {
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