#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/parser.h"
#define EXIT_SUCCESS 0 

int main(int argc, char* argv[]){
    char* filename = argv[1];
    if(argc != 2){
        printf("Error: Invalid number of arguments.\nUsage: %s <file.mtx>\n",argv[0]);
        return(EXIT_FAILURE);
    }

    char* path = "../matrices/";
    char* result = (char*) malloc(strlen(filename) + strlen(path) + 1);
    strcpy(result, path);
    strcat(result, filename);
    
    FILE* mtx = fopen(result, "r");
    if(mtx == NULL){
        printf("Error: Failed to open file %s: No such file or directory\n",filename);
        return(EXIT_FAILURE);
    }
    char buf[64];
    char* line;
    struct MtxType mtxType;
    parse_type(&mtxType, mtx);

    printf("%s\n", mtxType.object);        
}