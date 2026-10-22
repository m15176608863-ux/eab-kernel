#ifndef EAB2_TESTING_H
#define EAB2_TESTING_H

/* Test-only protocol: absent from the production DLL's exported symbols. */
#include "eab2/c_api.h"

#ifdef __cplusplus
extern "C" {
#endif

#define EAB2_ENCODING_BITS UINT32_C(1)
#define EAB2_ENCODING_RATIONAL UINT32_C(2)
#define EAB2_NUMERIC_ALLOW_UNDERFLOW UINT32_C(1)

#define EAB2_OP_SCALAR UINT32_C(1)
#define EAB2_OP_ALGEBRAIC_RATIONAL UINT32_C(2)
#define EAB2_OP_ALGEBRAIC_SQRT UINT32_C(3)
#define EAB2_OP_RATIO UINT32_C(4)
#define EAB2_OP_VECTOR UINT32_C(5)
#define EAB2_OP_SQRT UINT32_C(6)
#define EAB2_OP_NORM UINT32_C(7)
#define EAB2_OP_UNIT UINT32_C(8)
#define EAB2_OP_NORMALIZED_DIFFERENCE UINT32_C(9)
#define EAB2_OP_DECODE UINT32_C(10)
#define EAB2_OP_ORIENT2D UINT32_C(11)
#define EAB2_OP_CROSS2D UINT32_C(12)
#define EAB2_OP_DOT UINT32_C(13)
#define EAB2_OP_AABB2 UINT32_C(14)

typedef struct eab2_text {
    const char* data;
    uint64_t length;
} eab2_text;

typedef struct eab2_numeric_input {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t operation;
    uint32_t encoding;
    uint32_t flags;
    uint32_t reserved;
    uint64_t value_count;
    uint64_t value_stride;
    const eab2_text* values;
} eab2_numeric_input;

typedef struct eab2_numeric_output {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t call_status;
    uint32_t mathematical_status;
    uint32_t display_status;
    uint32_t reserved;
    uint64_t bits_capacity;
    uint64_t bits_count;
    uint64_t* bits;
} eab2_numeric_output;

typedef struct eab2_numeric_batch_input {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t item_count;
    uint64_t item_stride;
    const eab2_numeric_input* items;
} eab2_numeric_batch_input;

typedef struct eab2_numeric_batch_output {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t item_capacity;
    uint64_t item_stride;
    uint64_t item_count;
    eab2_numeric_output* items;
} eab2_numeric_batch_output;

/* Structural failure: no output mutation. Otherwise batch OK and per-item
 * status (including failures); bits written only for VALUE with DISPLAY_VALID
 * or explicit DISPLAY_UNDERFLOW_ZERO.
 * All strides are exactly sizeof(the corresponding element). */
EAB2_API eab2_call_status eab2_numeric_batch(
    eab2_context context, const eab2_numeric_batch_input* input,
    eab2_numeric_batch_output* output);

typedef struct eab2_point2_exact { eab2_text x; eab2_text y; } eab2_point2_exact;
typedef struct eab2_query2_exact_input {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t point_count; uint64_t point_stride;
    const eab2_point2_exact* points;
} eab2_query2_exact_input;
EAB2_API eab2_call_status eab2_query2_exact_batch(eab2_context context,
    eab2_entrance2 entrance, const eab2_query2_exact_input* input, eab2_query2_output* output);

/* NULL/0 window means unbounded; NULL/0 cone_tol/seg_tol mean Python defaults.
 * tol must be canonical nonnegative rational; require_in_segment is exactly 0/1. */
typedef struct eab2_covers2_input {
    uint32_t struct_size; uint32_t abi_version;
    uint32_t require_in_segment; uint32_t reserved;
    eab2_text window; eab2_text tol; eab2_text cone_tol; eab2_text seg_tol;
} eab2_covers2_input;
EAB2_API eab2_call_status eab2_covers2_exact(eab2_context context,
    eab2_entrance2 entrance, const eab2_covers2_input* input, eab2_exact_result* output);

#ifdef __cplusplus
}
#endif
#endif
