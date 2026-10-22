#include "eab2/c_api.h"
#include "eab2/testing.h"
#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <xmmintrin.h>

namespace {
unsigned checks = 0;
void check(bool ok, const char* what) { ++checks; if (!ok) throw std::runtime_error(what); }
template<class T> T init() { T v{}; v.struct_size = sizeof(v); v.abi_version = 1; return v; }
eab2_context context() {
    auto options = init<eab2_context_options>(); eab2_context result{};
    check(eab2_context_create(&options, &result) == 0, "context create"); return result;
}
eab2_point2_bits point(double x, double y) { return {std::bit_cast<uint64_t>(x), std::bit_cast<uint64_t>(y)}; }
eab2_body2 body(eab2_context ctx, double x = 0) {
    const eab2_point2_bits points[]{point(x,0),point(x+1,0),point(x+1,1),point(x,1)};
    auto input = init<eab2_body2_input>(); input.vertex_count=4; input.vertex_stride=sizeof(points[0]); input.vertices=points;
    eab2_body2 result{}; check(eab2_body2_create(ctx,&input,&result)==0,"body create"); return result;
}
std::string take(eab2_context ctx, eab2_exact_result& value) {
    check(value.call_status==0 && value.data && value.byte_count, "exact owned payload");
    std::string s(value.data,static_cast<size_t>(value.byte_count));
    check(eab2_result_destroy(ctx,value.result)==0,"result release");
    check(eab2_result_destroy(ctx,value.result)==EAB2_INVALID_HANDLE,"result stale"); return s;
}
void release_bad_fp() {
    const std::array<unsigned,11> modes{0x8000,0x0040,0x2000,0x4000,0x6000,7,8,9,10,11,12};
    for (const auto mode:modes) {
        auto ctx=context(); const auto a=body(ctx); auto opts=init<eab2_entrance2_options>();
        eab2_entrance2 ent{}; check(eab2_entrance2_create(ctx,a,a,&opts,&ent)==0,"release test entrance");
        auto exact=init<eab2_exact_result>(); check(eab2_local_origin2_exact(ctx,ent,&exact)==0,"release test result");
        const auto before=_mm_getcsr();
        const auto bad=mode>=7 && mode<=12 ? ((before & ~0x3fU) & ~(1U<<mode)) : (before|mode);
        _mm_setcsr(bad);
        auto limits=init<eab2_context_limits2>();
        const auto l=eab2_context_get_limits2(ctx,&limits);
        const auto r=eab2_result_destroy(ctx,exact.result);
        const auto e=eab2_entrance2_destroy(ctx,ent);
        const auto b=eab2_body2_destroy(ctx,a);
        const auto c=eab2_context_destroy(ctx);
        const auto after=_mm_getcsr(); _mm_setcsr(before);
        check(l==0 && r==0 && e==0 && b==0 && c==0,"release/get_limits under bad FP");
        check(after==bad,"release preserves host FP environment");
    }
}
void concurrent_contexts() {
    const auto a=context(), b=context();
    for (unsigned i=0;i<8;++i) {
        uint32_t first=99,second=99;
        std::thread one([&]{first=eab2_test_context_rendezvous(a);});
        std::thread two([&]{second=eab2_test_context_rendezvous(b);});
        one.join(); two.join();
        check(first==0 && second==0,"distinct contexts overlap while owning computation locks");
    }
    check(eab2_context_destroy(a)==0 && eab2_context_destroy(b)==0,"concurrency cleanup");
}
void l1_contract() {
    auto abi=init<eab2_c3l1_abi_info>(); check(eab2_get_c3l1_abi_info(&abi)==0,"C3 sizes");
    check(abi.assembly_body2_size==sizeof(eab2_assembly_body2) && abi.assembly2_input_size==sizeof(eab2_assembly2_input)
          && abi.lock2_input_size==sizeof(eab2_lock2_input),"C3 exact descriptor sizes");
    abi.reserved=1; check(eab2_get_c3l1_abi_info(&abi)==EAB2_INVALID_INPUT,"C3 reserved");
    const auto ctx=context(), other=context(); const auto a=body(ctx),b=body(ctx,1);
    std::array<eab2_assembly_body2,2> entries{init<eab2_assembly_body2>(),init<eab2_assembly_body2>()};
    entries[0].body=a; entries[1].body=b;
    entries[0].body_id={"a",1}; entries[1].body_id={"b",1};
    entries[0].dof_mask=7; entries[1].dof_mask=0; entries[1].boundary_type=EAB2_FIXED_BODY;
    entries[0].reference_point=point(7,-11); entries[0].dof_anchor=point(2,-3);
    eab2_pair2 pair{0,1}; auto input=init<eab2_assembly2_input>();
    input.flags=3; input.profile=1; input.body_count=2; input.body_stride=sizeof(entries[0]); input.bodies=entries.data();
    input.pair_count=1; input.pair_stride=sizeof(pair); input.pairs=&pair;
    eab2_assembly2 assembly{};
    for(unsigned k=0;k<9;++k) {
        auto bad=input; auto original=entries;
        if(k==0) --bad.struct_size;
        if(k==1) bad.flags=8;
        if(k==2) --bad.body_stride;
        if(k==3) bad.pair_count=0;
        if(k==4) entries[1].body_id=entries[0].body_id;
        if(k==5) entries[1].dof_mask=7;
        if(k==6) entries[0].dof_mask=8;
        if(k==7) entries[0].body_id={"\xc0\x80",2};
        if(k==8) bad.pair_stride=0;
        assembly=a;
        check(eab2_assembly2_create(ctx,&bad,&assembly)==EAB2_INVALID_INPUT && !assembly.id,"invalid assembly atomic token zero");
        entries=original;
    }
    auto unsupported=input; unsupported.profile=2;
    check(eab2_assembly2_create(ctx,&unsupported,&assembly)==EAB2_UNSUPPORTED,"unsupported profile");
    check(eab2_assembly2_create(other,&input,&assembly)==EAB2_INVALID_HANDLE,"assembly body ownership");
    check(eab2_assembly2_create(ctx,&input,&assembly)==0,"complete assembly snapshot");
    check(eab2_body2_destroy(ctx,a)==0 && eab2_body2_destroy(ctx,b)==0,"assembly owns copied geometry");
    eab2_contact_set2 contacts{}; check(eab2_assemble_contact_set2(ctx,assembly,&contacts)==0,"contact assembly");
    auto out=init<eab2_exact_result>();
    check(eab2_contact_set2_export_exact(ctx,contacts,&out)==0 && out.mathematical_status==EAB2_MATH_VALUE,"resolved contacts status");
    check(take(ctx,out).find("RESOLVED")!=std::string::npos,"contact export");
    auto request=init<eab2_lock2_input>(); uint64_t neighbor=1;
    request.neighbor_count=1; request.neighbor_stride=sizeof(neighbor); request.neighbors=&neighbor;
    out=init<eab2_exact_result>(); check(eab2_query_lock(ctx,assembly,&request,&out)==0,"query lock");
    check(take(ctx,out).find("REMOVABLE")!=std::string::npos,"lock separation status");
    request.moving_index=2; out=init<eab2_exact_result>(); const auto unchanged=out;
    check(eab2_query_lock(ctx,assembly,&request,&out)==EAB2_INVALID_INPUT && std::memcmp(&out,&unchanged,sizeof(out))==0,"lock invalid output unchanged");
    check(eab2_assembly2_destroy(ctx,assembly)==0,"contacts own copied assembly");
    check(eab2_first_order_mobility(ctx,contacts,&out)==0,"first order independent of released assembly");
    check(take(ctx,out).find("NONZERO_CONE")!=std::string::npos,"nonzero normal cone");
    out=init<eab2_exact_result>();
    const auto saved=_mm_getcsr(); _mm_setcsr(saved|0x8000);
    const auto failed=eab2_first_order_mobility(ctx,contacts,&out);
    const auto freed=eab2_contact_set2_destroy(ctx,contacts);
    const auto after=_mm_getcsr(); _mm_setcsr(saved);
    check(failed==EAB2_FP_CONTRACT && freed==0 && after==(saved|0x8000),"C3 FP failure and cleanup");
    check(eab2_first_order_mobility(ctx,contacts,&out)==EAB2_INVALID_HANDLE,"stale C3 handle");
    check(eab2_context_destroy(ctx)==0 && eab2_context_destroy(other)==0,"L1 cleanup");
}
void opt_contract() {
    const auto ctx=context(); const char* data[]{"1/1","1/1","-1/1"};
    std::array<eab2_text,3> values{};
    for(size_t i=0;i<3;++i) values[i]={data[i],std::strlen(data[i])};
    auto input=init<eab2_opt_input>(); input.rows=1;input.columns=1;input.max_pivots=10000;
    input.value_count=3;input.value_stride=sizeof(eab2_text);input.values=values.data();
    auto out=init<eab2_exact_result>();
    check(eab2_opt_solve_exact(ctx,&input,&out)==0 && out.mathematical_status==EAB2_MATH_VALUE,"optimal opt ABI");
    check(take(ctx,out).find("optimal")!=std::string::npos,"optimal opt JSON");
    values[1]={"-1/1",4}; out=init<eab2_exact_result>();
    check(eab2_opt_solve_exact(ctx,&input,&out)==0 && out.mathematical_status==EAB2_MATH_INFEASIBLE,"Farkas opt ABI"); take(ctx,out);
    input.rows=0;input.value_count=1;input.values=&values[2];out=init<eab2_exact_result>();
    check(eab2_opt_solve_exact(ctx,&input,&out)==0 && out.mathematical_status==EAB2_MATH_UNBOUNDED,"unbounded opt ABI");take(ctx,out);
    out=init<eab2_exact_result>(); auto before=out; input.value_count=0;
    check(eab2_opt_solve_exact(ctx,&input,&out)==EAB2_INVALID_INPUT && std::memcmp(&out,&before,sizeof(out))==0,"opt shape atomic failure");
    check(eab2_context_destroy(ctx)==0,"opt cleanup");
}
}
int main() {
    try { release_bad_fp(); concurrent_contexts(); l1_contract(); opt_contract();
        std::cout<<"EAB2_C3L1_ABI checks="<<checks<<" failed=0\n"; return 0;
    } catch(const std::exception& e) { std::cerr<<"EAB2_C3L1_ABI failed="<<e.what()<<" after="<<checks<<"\n"; return 1; }
}
