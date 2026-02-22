/*
 * This header files contains the structs and functions needed to parse a *.mtx file and generate its Coordinate Format.
 * The format of a *.mtx file is:
 * %%MatrixMarket <object> <format> <field> <symmetry>
 * % Comment lines (optional)
 * <nrows> <ncols> <nnz>
 * <i_1> <j_1> <value_1>
 * <i_2> <j_2> <value_2>
 * ...
 * <i_n> <j_n> <value_n>
 */

#ifndef PARSER_H   
#define PARSER_H

/*
 * Represents the metadata information of a SuiteSparse .mtx file.
 *
 * Fields:
 *     rows (int): The number of rows the matrix has.
 *     cols (int): The number of columns the matrix has.
 *     nnz (int): The number of non-zero elements.
 */
struct Metadata {
    int    rows;
    int    cols;
    int    nnz;
};

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
    char   name[16];
    char   object[16];
    char   format[16];
    char   field[16];
    char   symmetry[16];
};

/*
 * Represents the Coordinate Format of a Sparse Matrix.
 *
 * Fields:
 *     metadata (struct Metadata): Struct that contains information about the number of rows, cols and nnz.
 *     row_idx (int*):
 *     col_idx (int*):
 *     values (double*):
 */
struct COOMatrix {
    struct Metadata metadata;
    int    *row_idx;
    int    *col_idx;
    double *values;
};

/* This function parses the header line of a SuiteSparse .mtx file.
 * 
 * Args:
 *     mtxType (struct MtxType*): Pointer to a struct where the header information will be stored.
 *     file (FILE*): Pointer to an already open .mtx file.
 */
void parse_header(struct MtxType* mtx_type, FILE* file);

/* This function skips all the comment lines (starting with %) except the one with the name of the matrix.
 * Also it parses its metadata, which is in the line after the last comment. 
 * 
 * Args:
 *     mtx_type (struct MtxType*): Pointer to a struct where the header information will be stored.
 *     coo_mtx (struct COOMatrix*): Pointer to a struct that will create the COOMatrix format.
 *     file (FILE*): Pointer to an already open .mtx file.
 */
void parse_metadata(struct MtxType* mtx_type, struct COOMatrix* coo_mtx, FILE* file);

/* This function reads all the noncomment lines of the *.mtx file and generates the Coordinate Format of the matrix.
 * 
 * Args:
 *     mtx_type (struct MtxType*): Pointer to a struct where the header information will be stored.
 *     coo_mtx (struct COOMatrix*): Pointer to a struct that will create the COOMatrix format.
 *     file (FILE*): Pointer to an already open .mtx file.
 * 
 * Notes:
 *     - The function assumes that the function parse_metadata() has ran so that the struct Metadata metadata field has been initialized.
 *       If it is not initialized, memory cannot be allocated.
 *     - The FILE pointer points right at the beginning of the entries which share the format: row col value
 */
void parse_coo(struct COOMatrix* coo_mtx, FILE* file);

/* This function opens a files and exits if the file name does not exist.
 * 
 * Args:
 *     filename (char*): A String that represents the name of the file that will be opened.
 */
FILE* open_file(char* filename);

/* This function is used to concatinate the path into the matrices folder.
 * More presicely it concatinates the String "../matrices" (which represents the path to the folder where *.mtx files are saved) with the name of the .mtx file.
 * 
 * Args:
 *     filename (char*): A String that represents the name of the file that will be opened.
 */
char* reconstruct_path(char* filename);

#endif