#ifndef PARSER_H   
#define PARSER_H

/*
 * Represents the header information of a SuiteSparse .mtx file.
 *
 * Fields:
 *     name (char[16]): Optional name of the matrix (can store short titles or IDs).
 *     object (char[16]): Type of object in the file (usually "matrix").
 *     format (char[16]): Storage format (e.g., "coordinate" or "array").
 *     field (char[16]): Type of data in the matrix (e.g., "real", "integer", "complex").
 *     symmetry (char[16]): Symmetry property of the matrix ("general", "symmetric", etc.).
 */
struct MtxType{
    char name[16];
    char object[16];
    char format[16];
    char field[16];
    char symmetry[16];
};

/* Parses the header line of a SuiteSparse .mtx file.
 * 
 * Args:
 *     mtxType (struct MtxType*): Pointer to a struct where the header information will be stored.
 *     file (FILE*): Pointer to an already open .mtx file.
 */
void parse_type(struct MtxType* mtxType, FILE* file){
    fscanf(file, "%*s %15s %15s %15s %15s",
           mtxType->object, mtxType->format, mtxType->field, mtxType->symmetry);
    return;
}

#endif