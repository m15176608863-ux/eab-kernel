#ifndef EAB2_C_API_H
#define EAB2_C_API_H

#include <stdint.h>

#if defined(EAB2_BUILD_DLL)
#define EAB2_API __declspec(dllexport)
#elif defined(EAB2_STATIC)
#define EAB2_API
#else
#define EAB2_API __declspec(dllimport)
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define EAB2_ABI_VERSION UINT32_C(1)
#define EAB2_OK UINT32_C(0)
#define EAB2_INVALID_INPUT UINT32_C(1)
#define EAB2_INVALID_HANDLE UINT32_C(2)
#define EAB2_UNSUPPORTED UINT32_C(3)
#define EAB2_CONSTRUCTION_RANGE UINT32_C(4)
#define EAB2_RESOURCE_LIMIT UINT32_C(5)
#define EAB2_FP_CONTRACT UINT32_C(6)
#define EAB2_INTERNAL_ERROR UINT32_C(7)
#define EAB2_CANCELLED UINT32_C(8)

#define EAB2_MATH_NOT_COMPUTED UINT32_C(0)
#define EAB2_MATH_VALUE UINT32_C(1)
#define EAB2_MATH_UNPROVED UINT32_C(2)
#define EAB2_MATH_NO_EVENT UINT32_C(3)
#define EAB2_MATH_OVERLAP UINT32_C(4)
#define EAB2_MATH_INFEASIBLE UINT32_C(5)
#define EAB2_MATH_UNBOUNDED UINT32_C(6)

#define EAB2_DISPLAY_NOT_AVAILABLE UINT32_C(0)
#define EAB2_DISPLAY_VALID UINT32_C(1)
#define EAB2_DISPLAY_RANGE UINT32_C(2)

#define EAB2_CAP_CONTEXT UINT64_C(1)
#define EAB2_CAP_TEST_NUMERIC UINT64_C(2)
#define EAB2_CAP_RHO UINT64_C(65536)
#define EAB2_CAP_SE2 UINT64_C(131072)
#define EAB2_CAP_LP2 UINT64_C(262144)
#define EAB2_HANDLE_CONTEXT UINT32_C(1)

typedef uint32_t eab2_call_status;

/* A token, not a caller-owned pointer. All-zero is the only null token. */
typedef struct eab2_context {
    uint64_t owner;
    uint64_t id;
    uint64_t generation;
    uint32_t type;
    uint32_t reserved;
} eab2_context;

typedef struct eab2_abi_info {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t requested_capabilities;
    uint64_t supported_capabilities;
    uint64_t unsupported_capabilities;
    uint32_t context_size;
    uint32_t context_options_size;
    uint32_t error_info_size;
    uint32_t binary64_bits;
    uint32_t pointer_bits;
    uint32_t reserved;
    char build_identity[192];
} eab2_abi_info;

typedef struct eab2_context_options {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t flags;
    uint32_t reserved;
} eab2_context_options;

typedef struct eab2_error_info {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t code;
    uint32_t reserved;
    uint64_t index;
    char field[48];
} eab2_error_info;

EAB2_API eab2_call_status eab2_get_abi_info(eab2_abi_info* info);
EAB2_API eab2_call_status eab2_self_test(void);
EAB2_API eab2_call_status eab2_context_create(
    const eab2_context_options* options, eab2_context* output);
EAB2_API eab2_call_status eab2_context_destroy(eab2_context context);
/* required includes the NUL terminator. NULL/0 is a successful size query. */
EAB2_API eab2_call_status eab2_context_get_error(
    eab2_context context, eab2_error_info* info,
    char* message, uint64_t capacity, uint64_t* required);

#ifdef __cplusplus
}
#endif
#endif
