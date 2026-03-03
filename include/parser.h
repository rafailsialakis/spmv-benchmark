/*
 * This header file defines the data structures and functions required
 * to parse a Matrix Market (.mtx) file and represent it in Coordinate (COO) format.
 *
 * A Matrix Market file follows the structure below:
 *
 *   %%MatrixMarket <object> <format> <field> <symmetry>
 *   % Optional comment lines (each starting with '%')
 *   <nrows> <ncols> <nnz>
 *   <row_1> <col_1> <value_1>
 *   <row_2> <col_2> <value_2>
 *   ...
 *   <row_n> <col_n> <value_n>
 *
 * where:
 *   - <object>   : typically "matrix"
 *   - <format>   : usually "coordinate" (sparse representation)
 *   - <field>    : data type (e.g., real, integer, complex, pattern)
 *   - <symmetry> : symmetry type (e.g., general, symmetric, skew-symmetric, hermitian)
 *   - <nrows>    : number of matrix rows
 *   - <ncols>    : number of matrix columns
 *   - <nnz>      : number of non-zero entries
 *   - <row_i>, <col_i> : 1-based indices of the i-th non-zero element
 *   - <value_i>  : value of the i-th non-zero element (omitted if field = pattern)
 *
 * The Coordinate (COO) format stores the matrix as three parallel arrays:
 *   - row indices
 *   - column indices
 *   - corresponding non-zero values
 *
 * Note: Matrix Market indices are 1-based and may need conversion to 0-based
 * indexing depending on the internal representation.
 */

#ifndef    PARSER_H   
#define    PARSER_H
#define    IS_REAL(t)      (strcmp((t)->field,    "real")      == 0)
#define    IS_PATTERN(t)   (strcmp((t)->field,    "pattern")   == 0)
#define    IS_INTEGER(t)   (strcmp((t)->field,    "integer")   == 0)
#define    IS_COMPLEX(t)   (strcmp((t)->field,    "complex")   == 0)
#define    IS_SYMMETRIC(t) (strcmp((t)->symmetry, "symmetric") == 0)
#define    IS_GENERAL(t)   (strcmp((t)->symmetry, "general")   == 0)
#define    IS_SKEW(t)      (strcmp((t)->symmetry, "skew-symmetric") == 0)
#define    IS_COORDINATE(t)(strcmp((t)->format,   "coordinate") == 0)
#define    IS_ARRAY(t)     (strcmp((t)->format,   "array")      == 0)
#include   "coo.h"

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
* This function uses all the other functions in order to do the parsing of a *.mtx file into COO format. the header information of a SuiteSparse .mtx file.
* 
* Args:
*      filename (char*): A pointer to a String that represents the filename.
*
* Returns:
*      coo_mtx (struct COOMatrix*): A pointer to a COOMatrix struct that has been created based on the *.mtx file.
*/
struct COOMatrix* coo_parser(char* filename);

/* This function parses the header line of a SuiteSparse .mtx file.
* 
* Args:
*     mtx_type (struct MtxType*): Pointer to a struct where the header information will be stored.
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
void parse_coo(struct COOMatrix* coo_mtx, struct MtxType* mtx_type, FILE* file);

/* This function prints header/metadata information about the parsed matrix.
* 
* Args:
*     mtx_type (struct MtxType*): Pointer to a struct where the header information will be stored.
*     coo_mtx (struct COOMatrix*): Pointer to a struct that will create the COOMatrix format.
*/
void print_matrix_info(struct MtxType* mtx_type, struct COOMatrix* coo_mtx);

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