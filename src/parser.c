#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/parser.h"

struct COOMatrix* coo_parser(char* filename) {
    char* result = reconstruct_path(filename);
    FILE* mtx = open_file(result);

    struct MtxType* mtx_type = malloc(sizeof(struct MtxType));
    struct COOMatrix* coo_mtx = malloc(sizeof(struct COOMatrix));

    parse_header(mtx_type, mtx);
    parse_metadata(mtx_type, coo_mtx, mtx);
    parse_coo(coo_mtx, mtx_type, mtx);

    fclose(mtx);
    free(mtx_type);
    return coo_mtx;
}

void parse_header(struct MtxType* mtx_type, FILE* file){
    fscanf(file, "%*s %15s %15s %15s %15s\n",
           mtx_type->object, mtx_type->format, mtx_type->field, mtx_type->symmetry);
    return;
}

void parse_metadata(struct MtxType* mtx_type, struct COOMatrix* coo_mtx, FILE* file){
    char line[256];
    while (fgets(line, sizeof(line), file) != NULL) {
        // Skip comment lines except the line that saves the name.
        if (line[0] == '%'){
            sscanf(line, "%% name: %255s", mtx_type->name); 
            continue;
        }
        // Parse metadata line.
        sscanf(line, "%d %d %d", &coo_mtx->metadata.rows, &coo_mtx->metadata.cols, &coo_mtx->metadata.nnz);
        break;
    }
}

void print_matrix_info(struct MtxType* mtx_type, struct COOMatrix* coo_mtx) {
    printf("Matrix: %s\n",   mtx_type->name);
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

    // Temporary read stored indexes
    int*    tmp_row = malloc(nnz_stored * sizeof(int));
    int*    tmp_col = malloc(nnz_stored * sizeof(int));
    double* tmp_val = malloc(nnz_stored * sizeof(double));

    char line[256];
    for (int i = 0; i < nnz_stored; i++) {
        fgets(line, sizeof(line), file);
        sscanf(line, "%d %d %lf", &tmp_row[i], &tmp_col[i], &tmp_val[i]);
        tmp_row[i]--;
        tmp_col[i]--;
    }

    // Count nnz
    int real_nnz = nnz_stored;
    if (IS_SYMMETRIC(mtx_type))
        for (int i = 0; i < nnz_stored; i++)
            if (tmp_row[i] != tmp_col[i])
                real_nnz++;

    // Update metadata
    coo_mtx->metadata.nnz = real_nnz;

    // Allocate new nnz
    coo_mtx->row_idx = malloc(real_nnz * sizeof(int));
    coo_mtx->col_idx = malloc(real_nnz * sizeof(int));
    coo_mtx->values  = malloc(real_nnz * sizeof(double));

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