#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/parser.h"

int main(int argc, char* argv[]) {
    if (argc != 2) {
        printf("Error: Invalid number of arguments.\nUsage: %s <file.mtx>\n", argv[0]);
        return EXIT_FAILURE;
    }

    char* result = reconstruct_path(argv[1]);
    FILE* mtx = open_file(result);
    free(result);

    struct MtxType mtx_type = {0};
    struct COOMatrix coo_mtx = {0};

    parse_header(&mtx_type, mtx);
    parse_metadata(&mtx_type, &coo_mtx, mtx);
    parse_coo(&coo_mtx, mtx);

    fclose(mtx);
    free(coo_mtx.row_idx);
    free(coo_mtx.col_idx);
    free(coo_mtx.values);

    return EXIT_SUCCESS;
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
        sscanf(line, "%ld %ld %ld", &coo_mtx->metadata.rows, &coo_mtx->metadata.cols, &coo_mtx->metadata.nnz);
        break;
    }
}

void parse_coo(struct COOMatrix* coo_mtx, FILE* file) {
    coo_mtx->row_idx = malloc(sizeof(int)    * coo_mtx->metadata.nnz);
    coo_mtx->col_idx = malloc(sizeof(int)    * coo_mtx->metadata.nnz);
    coo_mtx->values  = malloc(sizeof(double) * coo_mtx->metadata.nnz);

    char line[256];
    for (int i = 0; i < coo_mtx->metadata.nnz; i++) {
        fgets(line, sizeof(line), file);
        sscanf(line, "%d %d %lf", &coo_mtx->row_idx[i],
                                   &coo_mtx->col_idx[i],
                                   &coo_mtx->values[i]);
        coo_mtx->row_idx[i]--;
        coo_mtx->col_idx[i]--;
        printf("%d %d %e\n", coo_mtx->row_idx[i],
                                   coo_mtx->col_idx[i],
                                   coo_mtx->values[i]);
    }
}

FILE* open_file(char* filename){
    FILE* f = fopen(filename, "r");
    if(f == NULL){
        printf("Error: Failed to open file %s: No such file or directory\n",filename);
        exit(EXIT_FAILURE);
    }
    return f;
}

char* reconstruct_path(char* filename){
    char* path = "../matrices/";
    char* result = (char*) malloc(strlen(filename) + strlen(path) + 1);
    strcpy(result, path);
    strcat(result, filename);
    return result;
}