#include "matrix/csr.h"
#include "reorder/reorder.h"
#include "rcm.h"

struct ColVal {
    int    col;
    double val;
};

static int cmp_col(const void* a, const void* b) {
    int ca = ((const struct ColVal*)a)->col;
    int cb = ((const struct ColVal*)b)->col;
    return (ca > cb) - (ca < cb);
}

static void build_graph_nodiag(struct CSRMatrix* csr, SCOTCH_Num** xadj_out, SCOTCH_Num** adjncy_out) {
    SCOTCH_Num n = csr->n;
    SCOTCH_Num* xadj   = malloc((size_t)(n + 1) * sizeof(SCOTCH_Num));
    SCOTCH_Num* adjncy = malloc((size_t)csr->nnz * sizeof(SCOTCH_Num));
    SCOTCH_Num pos = 0;
    xadj[0] = 0;
    for (SCOTCH_Num i = 0; i < n; i++) {
        for (int k = csr->row_ptr[i]; k < csr->row_ptr[i + 1]; k++)
            if (csr->col_idx[k] != i)
                adjncy[pos++] = csr->col_idx[k];
        xadj[i + 1] = pos;
    }
    *xadj_out = xadj;
    *adjncy_out = adjncy;
}

// Scotch context with the deterministic option and a fixed private seed.
// The default context is multi-threaded and gives a different result per run.
static void scotch_context_init(SCOTCH_Context* context) {
    SCOTCH_contextInit(context);
    SCOTCH_contextOptionSetNum(context, SCOTCH_OPTIONNUMDETERMINISTIC, 1);
    SCOTCH_contextRandomClone(context);
    SCOTCH_contextRandomSeed(context, SCOTCH_SEED);
}

int* compute_permutation_rcm(struct CSRMatrix* csr) {
    int n = csr->n;

    int* adj_row = malloc((size_t)(n + 1) * sizeof(int));
    int* adj     = malloc((size_t)csr->nnz * sizeof(int));
    int* perm    = malloc((size_t)n * sizeof(int));

    int pos = 0;
    for (int i = 0; i < n; i++) {
        adj_row[i] = pos + 1;
        for (int k = csr->row_ptr[i]; k < csr->row_ptr[i + 1]; k++)
            if (csr->col_idx[k] != i)
                adj[pos++] = csr->col_idx[k] + 1;
    }
    adj_row[n] = pos + 1;

    genrcm(n, pos, adj_row, adj, perm);     

    for (int i = 0; i < n; i++) perm[i]--;  

    free(adj_row);
    free(adj);
    return perm;
}

int* compute_permutation_gp(struct CSRMatrix* csr) {
    // Scotch k-way partitioning (the same call METIS_PartGraphKway wraps), run
    // in a deterministic context
    SCOTCH_Context context;
    SCOTCH_Graph   graph, ctx_graph;
    SCOTCH_Strat   strat;

    SCOTCH_Num n = csr->n;
    SCOTCH_Num *xadj, *adjncy;
    build_graph_nodiag(csr, &xadj, &adjncy);
    SCOTCH_Num* part = malloc((size_t)n * sizeof(SCOTCH_Num));

    scotch_context_init(&context);

    SCOTCH_graphInit(&graph);
    SCOTCH_stratInit(&strat);
    if (SCOTCH_graphBuild(&graph, 0, n, xadj, xadj + 1, NULL, NULL,
                          xadj[n], adjncy, NULL) != 0 ||
        SCOTCH_contextBindGraph(&context, &graph, &ctx_graph) != 0 ||
        SCOTCH_stratGraphMapBuild(&strat, SCOTCH_STRATDEFAULT, GP_PARTS, GP_IMBALANCE) != 0 ||
        SCOTCH_graphPart(&ctx_graph, GP_PARTS, &strat, part) != 0) {
        fprintf(stderr, "Scotch graph partitioning failed\n");
        exit(EXIT_FAILURE);
    }
    SCOTCH_graphExit(&ctx_graph);
    SCOTCH_stratExit(&strat);
    SCOTCH_graphExit(&graph);
    SCOTCH_contextExit(&context);

    // Group rows by part, keeping the original order inside each part
    int* cnt = calloc(GP_PARTS + 1, sizeof(int));
    for (SCOTCH_Num i = 0; i < n; i++) cnt[part[i] + 1]++;
    for (int k = 0; k < GP_PARTS; k++) cnt[k + 1] += cnt[k];

    int* p = malloc((size_t)n * sizeof(int));
    for (SCOTCH_Num i = 0; i < n; i++) p[cnt[part[i]]++] = (int)i;

    free(cnt); free(part); free(xadj); free(adjncy);
    return p;
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

int* compute_permutation_nd(struct CSRMatrix* csr) {
    // Scotch nested dissection (the same call METIS_NodeND wraps), run in a
    // deterministic context so the ordering is identical on every run
    SCOTCH_Context context;
    SCOTCH_Graph   graph, ctx_graph;
    SCOTCH_Strat   strat;
    SCOTCH_Ordering order;

    SCOTCH_Num n = csr->n;
    SCOTCH_Num *xadj, *adjncy;
    build_graph_nodiag(csr, &xadj, &adjncy);
    SCOTCH_Num* p  = malloc((size_t)n * sizeof(SCOTCH_Num));
    SCOTCH_Num* ip = malloc((size_t)n * sizeof(SCOTCH_Num));

    scotch_context_init(&context);
    SCOTCH_graphInit(&graph);
    SCOTCH_stratInit(&strat);
    if (SCOTCH_graphBuild(&graph, 0, n, xadj, xadj + 1, NULL, NULL,
                          xadj[n], adjncy, NULL) != 0 ||
        SCOTCH_contextBindGraph(&context, &graph, &ctx_graph) != 0 ||
        SCOTCH_graphOrderInit(&ctx_graph, &order, ip, p, NULL, NULL, NULL) != 0 ||
        SCOTCH_graphOrderCompute(&ctx_graph, &order, &strat) != 0) {
        fprintf(stderr, "Scotch nested dissection failed\n");
        exit(EXIT_FAILURE);
    }
    SCOTCH_graphOrderExit(&ctx_graph, &order);
    SCOTCH_graphExit(&ctx_graph);
    SCOTCH_stratExit(&strat);
    SCOTCH_graphExit(&graph);
    SCOTCH_contextExit(&context);

    free(ip); free(xadj); free(adjncy);
    // p[new] = old (Scotch peritab, METIS perm)
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
        new_csr->row_ptr[i+1] = csr->row_ptr[old_row+1] - csr->row_ptr[old_row];
    }

    // Calculate prefix sum
    for (int i = 1; i <= n; i++)
        new_csr->row_ptr[i] += new_csr->row_ptr[i-1];

    // Fill in col idx and value, sorted by the new column index so that every
    // matrix (original and reordered) reads x in ascending order within a row
    int max_row = 0;
    for (int i = 0; i < n; i++) {
        int len = csr->row_ptr[i+1] - csr->row_ptr[i];
        if (len > max_row) max_row = len;
    }
    struct ColVal* row = malloc((size_t)(max_row > 0 ? max_row : 1) * sizeof(struct ColVal));

    for (int i = 0; i < n; i++) {
        int old_row = p[i];
        int len     = 0;
        for (int j = csr->row_ptr[old_row]; j < csr->row_ptr[old_row+1]; j++) {
            row[len].col = inv_p[csr->col_idx[j]];
            row[len].val = csr->values[j];
            len++;
        }
        qsort(row, len, sizeof(struct ColVal), cmp_col);

        int new_pos = new_csr->row_ptr[i];
        for (int k = 0; k < len; k++) {
            new_csr->col_idx[new_pos + k] = row[k].col;
            new_csr->values[new_pos + k]  = row[k].val;
        }
    }

    free(row);
    free(inv_p);
    return new_csr;
}