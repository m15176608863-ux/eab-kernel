#include "eab2/c_api.h"
#include <stdio.h>
#include <string.h>

#define INIT(v) do { memset(&(v), 0, sizeof(v)); (v).struct_size=sizeof(v); (v).abi_version=EAB2_ABI_VERSION; } while (0)
#define CHECK(condition) do { ++checks; if (!(condition)) { printf("C_HEADER failure=%u\n",checks); return 1; } } while (0)
int main(void) {
    unsigned checks=0;
    eab2_abi_info info; eab2_context_options options; eab2_context context;
    eab2_body2_input body_input; eab2_body2 body; eab2_entrance2_options eoptions; eab2_entrance2 entrance;
    eab2_point2_bits triangle[3]={{0,0},{UINT64_C(0x3ff0000000000000),0},{0,UINT64_C(0x3ff0000000000000)}};
    eab2_query2_input query; eab2_query2_output query_out; eab2_query2_item item; eab2_exact_result exact;
    eab2_context_limits2 limits; eab2_c1_abi_info c1; eab2_c3l1_abi_info c3;
    eab2_assembly_body2 entry; eab2_assembly2_input assembly_input; eab2_assembly2 assembly;
    eab2_contact_set2 contacts; eab2_lock2_input lock_input;
    INIT(info); info.requested_capabilities=EAB2_CAP_CONTEXT|EAB2_CAP_LIMITS2|EAB2_CAP_ASSEMBLY2|EAB2_CAP_CONTACTSET2|EAB2_CAP_LOCK2|EAB2_CAP_MOBILITY2;
    CHECK(eab2_get_abi_info(&info)==EAB2_OK);
    CHECK(info.context_size==sizeof(context) && info.binary64_bits==64);
    CHECK(!(info.supported_capabilities & (EAB2_CAP_TEST_NUMERIC|EAB2_CAP_TEST_EXACT2|EAB2_CAP_TEST_OPT)));
    CHECK(eab2_self_test()==EAB2_OK);
    INIT(options); CHECK(eab2_context_create(&options,&context)==EAB2_OK);
    INIT(c1); CHECK(eab2_get_c1_abi_info(&c1)==EAB2_OK);
    INIT(c3); CHECK(eab2_get_c3l1_abi_info(&c3)==EAB2_OK);
    INIT(limits); CHECK(eab2_context_get_limits2(context,&limits)==EAB2_OK);
    INIT(body_input); body_input.vertex_count=3;body_input.vertex_stride=sizeof(triangle[0]);body_input.vertices=triangle;
    CHECK(eab2_body2_create(context,&body_input,&body)==EAB2_OK);
    INIT(eoptions); CHECK(eab2_entrance2_create(context,body,body,&eoptions,&entrance)==EAB2_OK);
    INIT(query); query.point_count=1;query.point_stride=sizeof(triangle[0]);query.points=triangle;
    INIT(query_out); query_out.item_capacity=1;query_out.item_stride=sizeof(item);query_out.items=&item;
    CHECK(eab2_query2_batch(context,entrance,&query,&query_out)==EAB2_OK && item.body_state==EAB2_BODY_OVERLAP);
    CHECK(eab2_membership2_batch(context,entrance,&query,&query_out)==EAB2_OK);
    CHECK(eab2_topology2_batch(context,entrance,&query,&query_out)==EAB2_OK);
    INIT(exact); CHECK(eab2_local_origin2_exact(context,entrance,&exact)==EAB2_OK && exact.byte_count>0);
    CHECK(eab2_result_destroy(context,exact.result)==EAB2_OK);
    INIT(exact); CHECK(eab2_result_export_exact(context,entrance,&exact)==EAB2_OK && exact.byte_count>0);
    CHECK(eab2_result_destroy(context,exact.result)==EAB2_OK);
    INIT(entry);entry.body=body;entry.body_id.data="free";entry.body_id.length=4;entry.dof_mask=7;
    INIT(assembly_input);assembly_input.flags=EAB2_ASSEMBLY_COMPLETE|EAB2_ASSEMBLY_EXPLICIT_PAIRS;assembly_input.profile=1;
    assembly_input.body_count=1;assembly_input.body_stride=sizeof(entry);assembly_input.bodies=&entry;assembly_input.pair_stride=sizeof(eab2_pair2);
    CHECK(eab2_assembly2_create(context,&assembly_input,&assembly)==EAB2_OK);
    CHECK(eab2_assemble_contact_set2(context,assembly,&contacts)==EAB2_OK);
    INIT(exact);CHECK(eab2_contact_set2_export_exact(context,contacts,&exact)==EAB2_OK);
    CHECK(eab2_result_destroy(context,exact.result)==EAB2_OK);
    INIT(lock_input);lock_input.neighbor_stride=sizeof(uint64_t);INIT(exact);
    CHECK(eab2_query_lock(context,assembly,&lock_input,&exact)==EAB2_OK);
    CHECK(eab2_result_destroy(context,exact.result)==EAB2_OK);
    INIT(exact);CHECK(eab2_first_order_mobility(context,contacts,&exact)==EAB2_OK);
    CHECK(eab2_result_destroy(context,exact.result)==EAB2_OK);
    CHECK(eab2_contact_set2_destroy(context,contacts)==EAB2_OK);
    CHECK(eab2_assembly2_destroy(context,assembly)==EAB2_OK);
    CHECK(eab2_entrance2_destroy(context,entrance)==EAB2_OK);
    CHECK(eab2_body2_destroy(context,body)==EAB2_OK);
    CHECK(eab2_context_destroy(context)==EAB2_OK);
    CHECK(eab2_context_destroy(context)==EAB2_INVALID_HANDLE);
#ifdef EAB2_STATIC
    printf("C_HEADER_STATIC checks=%u failures=0\n",checks);
#else
    printf("C_HEADER_PRODUCTION_DLL checks=%u failures=0\n",checks);
#endif
    return 0;
}
