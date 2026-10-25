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

#define EAB2_MATH_MECHANICAL_UNRESOLVED UINT32_C(7)

#define EAB2_DISPLAY_NOT_AVAILABLE UINT32_C(0)
#define EAB2_DISPLAY_VALID UINT32_C(1)
#define EAB2_DISPLAY_RANGE UINT32_C(2)
#define EAB2_DISPLAY_UNDERFLOW_ZERO UINT32_C(3)

#define EAB2_CAP_CONTEXT UINT64_C(1)
#define EAB2_CAP_TEST_NUMERIC UINT64_C(2)
#define EAB2_CAP_BODY2 UINT64_C(4)
#define EAB2_CAP_ENTRANCE2 UINT64_C(8)
#define EAB2_CAP_QUERY2 UINT64_C(16)
#define EAB2_CAP_EXPORT_EXACT UINT64_C(32)
#define EAB2_CAP_LOCAL2 UINT64_C(64)
#define EAB2_CAP_TEST_EXACT2 UINT64_C(128)
#define EAB2_CAP_LIMITS2 UINT64_C(256)
#define EAB2_CAP_ASSEMBLY2 UINT64_C(512)
#define EAB2_CAP_CONTACTSET2 UINT64_C(1024)
#define EAB2_CAP_LOCK2 UINT64_C(2048)
#define EAB2_CAP_MOBILITY2 UINT64_C(4096)
#define EAB2_CAP_TEST_OPT UINT64_C(8192)
#define EAB2_CAP_LIMIT2 UINT64_C(16384)
#define EAB2_CAP_CRITICAL_PARAMETER UINT64_C(32768)
#define EAB2_CAP_RHO UINT64_C(65536)
#define EAB2_CAP_SE2 UINT64_C(131072)
#define EAB2_CAP_LP2 UINT64_C(262144)
#define EAB2_CAP_SENSITIVITY2 UINT64_C(524288)
#define EAB2_HANDLE_CONTEXT UINT32_C(1)
#define EAB2_HANDLE_BODY2 UINT32_C(2)
#define EAB2_HANDLE_ENTRANCE2 UINT32_C(3)
#define EAB2_HANDLE_RESULT UINT32_C(4)
#define EAB2_HANDLE_ASSEMBLY2 UINT32_C(5)
#define EAB2_HANDLE_CONTACTSET2 UINT32_C(6)
#define EAB2_BODY_OUTSIDE UINT32_C(0)
#define EAB2_BODY_CONTACT UINT32_C(1)
#define EAB2_BODY_OVERLAP UINT32_C(2)
#define EAB2_TOPOLOGY_OUTSIDE UINT32_C(0)
#define EAB2_TOPOLOGY_BOUNDARY UINT32_C(1)
#define EAB2_TOPOLOGY_INTERIOR UINT32_C(2)
#define EAB2_ENTRANCE_NO_MERGE UINT32_C(1)
#define EAB2_ENTRANCE_NO_COMPACT UINT32_C(2)
#define EAB2_ENTRANCE_NO_CACHE UINT32_C(4)

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


/* Positive explicit values only; query defaults before configuration. */
typedef struct eab2_context_limits2 {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t max_work_units; uint64_t max_elements; uint64_t max_integer_bits;
} eab2_context_limits2;
EAB2_API eab2_call_status eab2_context_get_limits2(eab2_context context, eab2_context_limits2* output);
EAB2_API eab2_call_status eab2_context_configure_limits2(eab2_context context, const eab2_context_limits2* input);

/* C1 working interface. Tokens share a layout, but their types are checked. */
typedef eab2_context eab2_body2;
typedef eab2_context eab2_entrance2;
typedef eab2_context eab2_result;
typedef struct eab2_point2_bits { uint64_t x_bits; uint64_t y_bits; } eab2_point2_bits;
typedef struct eab2_body2_input {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t vertex_count; uint64_t vertex_stride;
    const eab2_point2_bits* vertices;
    uint32_t flags; uint32_t reserved;
} eab2_body2_input;
typedef struct eab2_entrance2_options {
    uint32_t struct_size; uint32_t abi_version;
    uint32_t flags; uint32_t reserved;
} eab2_entrance2_options;
typedef struct eab2_query2_input {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t point_count; uint64_t point_stride;
    const eab2_point2_bits* points;
} eab2_query2_input;
typedef struct eab2_query2_item {
    uint32_t call_status; uint32_t mathematical_status;
    uint32_t body_state; uint32_t topology_state;
} eab2_query2_item;
typedef struct eab2_query2_output {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t item_capacity; uint64_t item_stride; uint64_t item_count;
    eab2_query2_item* items;
} eab2_query2_output;
typedef struct eab2_exact_result {
    uint32_t struct_size; uint32_t abi_version;
    uint32_t call_status; uint32_t mathematical_status;
    eab2_result result;
    const char* data; uint64_t byte_count;
} eab2_exact_result;
typedef struct eab2_c1_abi_info {
    uint32_t struct_size; uint32_t abi_version;
    uint32_t body2_input_size; uint32_t entrance2_options_size;
    uint32_t query2_input_size; uint32_t query2_item_size;
    uint32_t query2_output_size; uint32_t exact_result_size;
    uint32_t point2_bits_size; uint32_t reserved;
} eab2_c1_abi_info;
EAB2_API eab2_call_status eab2_get_c1_abi_info(eab2_c1_abi_info* info);
EAB2_API eab2_call_status eab2_body2_create(eab2_context context,
    const eab2_body2_input* input, eab2_body2* output);
EAB2_API eab2_call_status eab2_body2_destroy(eab2_context context, eab2_body2 body);
EAB2_API eab2_call_status eab2_entrance2_create(eab2_context context,
    eab2_body2 a, eab2_body2 b, const eab2_entrance2_options* options, eab2_entrance2* output);
EAB2_API eab2_call_status eab2_entrance2_destroy(eab2_context context, eab2_entrance2 entrance);
/* Both states are returned together; no single inside Boolean substitutes for either. */
EAB2_API eab2_call_status eab2_query2_batch(eab2_context context, eab2_entrance2 entrance,
    const eab2_query2_input* input, eab2_query2_output* output);
EAB2_API eab2_call_status eab2_membership2_batch(eab2_context context, eab2_entrance2 entrance,
    const eab2_query2_input* input, eab2_query2_output* output);
EAB2_API eab2_call_status eab2_topology2_batch(eab2_context context, eab2_entrance2 entrance,
    const eab2_query2_input* input, eab2_query2_output* output);
/* UTF-8 JSON, byte_count excludes terminating NUL. Valid until result/context destroy. */
EAB2_API eab2_call_status eab2_result_export_exact(eab2_context context,
    eab2_entrance2 entrance, eab2_exact_result* output);
EAB2_API eab2_call_status eab2_local_origin2_exact(eab2_context context,
    eab2_entrance2 entrance, eab2_exact_result* output);
EAB2_API eab2_call_status eab2_result_destroy(eab2_context context, eab2_result result);

/* C3-L1 working ABI; exact JSON is owned by a result handle. */
typedef eab2_context eab2_assembly2;
typedef eab2_context eab2_contact_set2;
typedef struct eab2_string { const char* data; uint64_t length; } eab2_string;
#define EAB2_BOUNDARY_NONE UINT32_C(0)
#define EAB2_FIXED_BODY UINT32_C(1)
#define EAB2_FORCE_CONTROLLED_PLATE UINT32_C(2)
#define EAB2_PROFILE1 UINT32_C(1)
#define EAB2_ASSEMBLY_COMPLETE UINT32_C(1)
#define EAB2_ASSEMBLY_EXPLICIT_PAIRS UINT32_C(2)
/* EAB2_ASSEMBLY_COMPLETE must be combined with EAB2_ASSEMBLY_EXPLICIT_PAIRS
   (flags = 3); flags = 1 alone is rejected as INVALID_INPUT. */
/* Mask bit 0=x, bit 1=y, bit 2=rotation; 1 means free. Both points explicit. */
typedef struct eab2_assembly_body2 {
    uint32_t struct_size; uint32_t abi_version;
    eab2_body2 body;
    eab2_string body_id;
    eab2_point2_bits reference_point; eab2_point2_bits dof_anchor;
    uint32_t boundary_type; uint32_t dof_mask;
} eab2_assembly_body2;
typedef struct eab2_pair2 { uint64_t a; uint64_t b; } eab2_pair2;
typedef struct eab2_assembly2_input {
    uint32_t struct_size; uint32_t abi_version;
    uint32_t flags; uint32_t profile;
    uint64_t body_count; uint64_t body_stride; const eab2_assembly_body2* bodies;
    uint64_t pair_count; uint64_t pair_stride; const eab2_pair2* pairs;
} eab2_assembly2_input;
/* Explicit neighbor indices, each treated as fixed for this translation query.
 * No omitted neighbor is assumed absent; this is not an assembly mobility test. */
typedef struct eab2_lock2_input {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t moving_index;
    uint64_t neighbor_count; uint64_t neighbor_stride; const uint64_t* neighbors;
} eab2_lock2_input;
typedef struct eab2_c3l1_abi_info {
    uint32_t struct_size; uint32_t abi_version;
    uint32_t assembly_body2_size; uint32_t assembly2_input_size;
    uint32_t pair2_size; uint32_t lock2_input_size;
    uint32_t string_size; uint32_t reserved;
} eab2_c3l1_abi_info;
EAB2_API eab2_call_status eab2_get_c3l1_abi_info(eab2_c3l1_abi_info* info);
EAB2_API eab2_call_status eab2_assembly2_create(eab2_context context,
    const eab2_assembly2_input* input, eab2_assembly2* output);
EAB2_API eab2_call_status eab2_assembly2_destroy(eab2_context context, eab2_assembly2 assembly);
EAB2_API eab2_call_status eab2_assemble_contact_set2(eab2_context context,
    eab2_assembly2 assembly, eab2_contact_set2* output);
EAB2_API eab2_call_status eab2_contact_set2_destroy(eab2_context context, eab2_contact_set2 contacts);
EAB2_API eab2_call_status eab2_contact_set2_export_exact(eab2_context context,
    eab2_contact_set2 contacts, eab2_exact_result* output);
EAB2_API eab2_call_status eab2_query_lock(eab2_context context, eab2_assembly2 assembly,
    const eab2_lock2_input* input, eab2_exact_result* output);
EAB2_API eab2_call_status eab2_first_order_mobility(eab2_context context,
    eab2_contact_set2 contacts, eab2_exact_result* output);

/* C3-L3 working ABI. Loads are wrenches about each frozen reference_point,
 * in the exact body order of the ContactSet2 assembly; fixed-body loads are
 * retained but do not create equilibrium rows. All scalar inputs are finite
 * binary64 bit patterns. No rational threshold is rounded back into an input. */
typedef struct eab2_body_load2 {
    uint64_t dead_bits[3]; uint64_t live_bits[3];
} eab2_body_load2;
typedef struct eab2_limit2_input {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t mu_bits;
    uint64_t body_count; uint64_t body_stride; const eab2_body_load2* loads;
} eab2_limit2_input;
#define EAB2_PARAMETER_MU UINT32_C(1)
typedef struct eab2_critical_parameter_input {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t mu_max_bits; uint64_t max_steps;
    uint64_t body_count; uint64_t body_stride; const eab2_body_load2* loads;
    uint32_t parameter; uint32_t reserved;
} eab2_critical_parameter_input;
typedef struct eab2_c3l3_abi_info {
    uint32_t struct_size; uint32_t abi_version;
    uint32_t body_load2_size; uint32_t limit2_input_size;
    uint32_t critical_parameter_input_size; uint32_t reserved;
} eab2_c3l3_abi_info;
EAB2_API eab2_call_status eab2_get_c3l3_abi_info(eab2_c3l3_abi_info* info);
/* Atomic result publication: failed calls leave output unchanged. Successful
 * unresolved/UNPROVED/INFEASIBLE/UNBOUNDED results still have call_status=OK.
 * The exact JSON and result token follow result_destroy ownership rules. */
EAB2_API eab2_call_status eab2_solve_limit2(eab2_context context,
    eab2_contact_set2 contacts, const eab2_limit2_input* input, eab2_exact_result* output);
EAB2_API eab2_call_status eab2_critical_parameter(eab2_context context,
    eab2_contact_set2 contacts, const eab2_critical_parameter_input* input, eab2_exact_result* output);

/* C3-L4: exact seed channels, bound to a retained solve_limit2 or
 * critical_parameter result token. No primal/critical re-solve occurs.
 * Strings have explicit byte lengths. Exact values are reduced n/d, d>0.
 * Every stride must equal sizeof(the element), not merely be large enough. */
typedef struct eab2_string_array {
    uint64_t value_count; uint64_t value_stride; const eab2_string* values;
} eab2_string_array;
typedef struct eab2_sensitivity_vertex2 {
    eab2_string body_id; uint64_t vertex_id;
} eab2_sensitivity_vertex2;
typedef struct eab2_sensitivity_channel2 {
    uint32_t struct_size; uint32_t abi_version;
    eab2_string parameter;
    uint32_t positive_direction_valid; uint32_t negative_direction_valid;
    eab2_string_array validity_conditions; eab2_string_array tied_labels;
} eab2_sensitivity_channel2;
typedef struct eab2_sensitivity2_input {
    uint32_t struct_size; uint32_t abi_version;
    uint64_t parameter_count; uint64_t output_count; uint64_t channel_count;
    uint64_t body_count; uint64_t vertex_count;
    uint64_t channel_stride; const eab2_sensitivity_channel2* channels;
    eab2_string_array body_ids;
    uint64_t vertex_stride; const eab2_sensitivity_vertex2* vertex_ids;
    eab2_string_array vertices; eab2_string_array dead; eab2_string_array live;
    eab2_string_array dof_anchor; eab2_string_array mu;
} eab2_sensitivity2_input;
typedef struct eab2_c3l4_abi_info {
    uint32_t struct_size; uint32_t abi_version;
    uint32_t string_array_size; uint32_t sensitivity_vertex2_size;
    uint32_t sensitivity_channel2_size; uint32_t sensitivity2_input_size;
    uint32_t reserved; uint32_t reserved2;
} eab2_c3l4_abi_info;
/* v1: P>=1, output_count=1, channel_count=P; distinct parameter names.
 * body_ids sorted by UTF-8 body ID, vertex_ids by (body ID, original ID),
 * both exactly equal the retained snapshot. Fixed row-major seed shapes:
 * vertices[P][V][2], dead/live[P][B][3], dof_anchor[P][B][2], mu[P].
 * Caller tied_labels are strings; derived critical labels stay structured.
 * JSON has explicit counts and a [output][channel] row-major Jacobian;
 * unavailable/non-smooth Jacobian elements are null, not fabricated zero.
 * Failure leaves output unchanged. Result/context destruction owns cleanup. */
EAB2_API eab2_call_status eab2_get_c3l4_abi_info(eab2_c3l4_abi_info* info);
EAB2_API eab2_call_status eab2_evaluate_sensitivity2(eab2_context context,
    eab2_result base_result, const eab2_sensitivity2_input* input, eab2_exact_result* output);

#ifdef __cplusplus
}
#endif
#endif
