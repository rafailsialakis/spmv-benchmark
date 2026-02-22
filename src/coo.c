#include <stdio.h>
#include <stdlib.h>
#include "../include/coo.h"

void coo_free(struct COOMatrix* coo){
    free(coo->col_idx);
    free(coo->row_idx);
    free(coo->values);
}