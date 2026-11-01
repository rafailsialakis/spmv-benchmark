#include <limits.h>
#include "matrix/parser.h"

// Every parse error stops the run: a silently mis-read matrix would still
// pass the permutation check (it only compares the matrix with itself).
static void parse_fail(const char* what, long line) {
    if (line > 0)
        fprintf(stderr, "Matrix Market parse error (line %ld): %s\n", line, what);
    else
        fprintf(stderr, "Matrix Market parse error: %s\n", what);
    exit(EXIT_FAILURE);
}

struct COOMatrix* coo_parser(char* filename) {
    char* result = reconstruct_path(filename);
    FILE* mtx = open_file(result);

    struct MtxType* mtx_type = calloc(1, sizeof(struct MtxType));
    struct COOMatrix* coo_mtx = malloc(sizeof(struct COOMatrix));

    parse_header(mtx_type, mtx);
    parse_metadata(mtx_type, coo_mtx, mtx);
    parse_coo(coo_mtx, mtx_type, mtx);

    fclose(mtx);
    free(mtx_type);
    return coo_mtx;
}

void parse_header(struct MtxType* mtx_type, FILE* file){
    char banner[32] = {0};
    if (fscanf(file, "%31s %15s %15s %15s %15s", banner,
               mtx_type->object, mtx_type->format, mtx_type->field, mtx_type->symmetry) != 5)
        parse_fail("incomplete %%MatrixMarket header", 1);
    if (strcasecmp(banner, "%%MatrixMarket") != 0)
        parse_fail("missing %%MatrixMarket banner", 1);
    if (strcasecmp(mtx_type->object, "matrix") != 0 || strcasecmp(mtx_type->format, "coordinate") != 0)
        parse_fail("only 'matrix coordinate' files are supported", 1);
    // pattern files have no values and complex needs another kernel
    if (!IS_REAL(mtx_type) && !IS_INTEGER(mtx_type))
        parse_fail("field must be 'real' or 'integer' (pattern/complex not supported)", 1);
    // skew-symmetric/hermitian would need a sign/conjugate when mirroring
    if (!IS_SYMMETRIC(mtx_type) && !IS_GENERAL(mtx_type))
        parse_fail("symmetry must be 'general' or 'symmetric'", 1);
    // consume the rest of the header line
    int c;
    while ((c = fgetc(file)) != '\n' && c != EOF) {}
}

void parse_metadata(struct MtxType* mtx_type, struct COOMatrix* coo_mtx, FILE* file){
    char line[512];
    long lineno = 1;
    while (fgets(line, sizeof(line), file) != NULL) {
        lineno++;
        // Skip comment lines except the line that saves the name.
        if (line[0] == '%'){
            sscanf(line, "%% name: %127s", mtx_type->name);
            continue;
        }
        if (sscanf(line, "%d %d %d", &coo_mtx->metadata.rows,
                   &coo_mtx->metadata.cols, &coo_mtx->metadata.nnz) != 3)
            parse_fail("size line must contain rows, cols and nnz", lineno);
        if (coo_mtx->metadata.rows <= 0 || coo_mtx->metadata.nnz < 0)
            parse_fail("invalid matrix dimensions", lineno);
        if (coo_mtx->metadata.rows != coo_mtx->metadata.cols)
            parse_fail("matrix must be square", lineno);
        return;
    }
    parse_fail("missing size line", lineno);
}

void print_matrix_info(struct MtxType* mtx_type, struct COOMatrix* coo_mtx) {
    printf("\nMatrix: %s\n",   mtx_type->name);
    printf("Format: %s\n",   mtx_type->format);
    printf("Field:  %s\n",   mtx_type->field);
    printf("Symmetry: %s\n", mtx_type->symmetry);
    printf("Rows: %d, Cols: %d, NNZ: %d\n",
           coo_mtx->metadata.rows,
           coo_mtx->metadata.cols,
           coo_mtx->metadata.nnz);
}

void parse_coo(struct COOMatrix* coo_mtx, struct MtxType* mtx_type, FILE* file) {
    int nnz_stored = coo_mtx->metadata.nnz;
    int n = coo_mtx->metadata.rows;

    // Temporary read stored indexes
    int*    tmp_row = malloc((size_t)nnz_stored * sizeof(int));
    int*    tmp_col = malloc((size_t)nnz_stored * sizeof(int));
    double* tmp_val = malloc((size_t)nnz_stored * sizeof(double));

    char line[512];
    for (int i = 0; i < nnz_stored; i++) {
        if (fgets(line, sizeof(line), file) == NULL)
            parse_fail("file ends before all nnz entries were read", -1);
        if (sscanf(line, "%d %d %lf", &tmp_row[i], &tmp_col[i], &tmp_val[i]) != 3)
            parse_fail("entry must contain row, col and value", -1);
        if (tmp_row[i] < 1 || tmp_row[i] > n || tmp_col[i] < 1 || tmp_col[i] > n)
            parse_fail("entry index out of range", -1);
        tmp_row[i]--;
        tmp_col[i]--;
    }

    // Count nnz
    long long real_nnz = nnz_stored;
    if (IS_SYMMETRIC(mtx_type))
        for (int i = 0; i < nnz_stored; i++)
            if (tmp_row[i] != tmp_col[i])
                real_nnz++;
    if (real_nnz > INT_MAX)
        parse_fail("expanded nnz does not fit in int", -1);

    // Update metadata
    coo_mtx->metadata.nnz = (int)real_nnz;

    // Allocate new nnz
    coo_mtx->row_idx = malloc((size_t)real_nnz * sizeof(int));
    coo_mtx->col_idx = malloc((size_t)real_nnz * sizeof(int));
    coo_mtx->values  = malloc((size_t)real_nnz * sizeof(double));

    // Fill COO
    int idx = 0;
    for (int i = 0; i < nnz_stored; i++) {
        coo_mtx->row_idx[idx] = tmp_row[i];
        coo_mtx->col_idx[idx] = tmp_col[i];
        coo_mtx->values[idx]  = tmp_val[i];
        idx++;

        // If is symmetric & non-diagonal
        if (IS_SYMMETRIC(mtx_type) && tmp_row[i] != tmp_col[i]) {
            coo_mtx->row_idx[idx] = tmp_col[i];
            coo_mtx->col_idx[idx] = tmp_row[i];
            coo_mtx->values[idx]  = tmp_val[i];
            idx++;
        }
    }
    print_matrix_info(mtx_type, coo_mtx);
    free(tmp_row);
    free(tmp_col);
    free(tmp_val);
}

FILE* open_file(char* filename){
    FILE* f = fopen(filename, "r"); 
    if(f == NULL){
        printf("Error: Failed to open file %s: No such file or directory\n",filename);
        exit(EXIT_FAILURE);
    }
    free(filename);
    return f;
}

char* reconstruct_path(char* filename){
    char* path = "matrices/";
    // Memory allocation for result (+1 for \0);
    char* result = (char*) malloc(strlen(filename) + strlen(path) + 1);
    strcpy(result, path);
    strcat(result, filename);
    return result;
}
