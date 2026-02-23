#include <stdio.h>
#include "../include/parser.h"
#include "../include/csr.h"

int main(int argc, char* argv[]){
    struct COOMatrix* coo_mtx = coo_parser(argv[1]);
    struct CSRMatrix* csr_matrix = csr_from_coo(coo_mtx);
    
    coo_free(coo_mtx);
    //csr_free(csr);
}