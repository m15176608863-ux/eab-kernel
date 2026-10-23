#include "eab2/c_api.h"
#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <xmmintrin.h>

namespace {
unsigned checks = 0;
void check(bool ok, const char* what) { ++checks; if (!ok) throw std::runtime_error(what); }
template<class T> T init() { T v{}; v.struct_size=sizeof(v); v.abi_version=EAB2_ABI_VERSION; return v; }
uint64_t bits(double v) { return std::bit_cast<uint64_t>(v); }
eab2_point2_bits point(double x,double y) { return {bits(x),bits(y)}; }
eab2_context context() {
    auto options=init<eab2_context_options>(); eab2_context ctx{};
    check(eab2_context_create(&options,&ctx)==0,"context create"); return ctx;
}
eab2_body2 box(eab2_context ctx, double x, double y) {
    const eab2_point2_bits pts[]{point(x,y),point(x+1,y),point(x+1,y+1),point(x,y+1)};
    auto input=init<eab2_body2_input>(); input.vertex_count=4;input.vertex_stride=sizeof(pts[0]);input.vertices=pts;
    eab2_body2 body{}; check(eab2_body2_create(ctx,&input,&body)==0,"body create");return body;
}
eab2_contact_set2 isolated(eab2_context ctx, bool complete=true, bool corner=false) {
    std::array<eab2_assembly_body2,2> items{init<eab2_assembly_body2>(),init<eab2_assembly_body2>()};
    items[0].body=box(ctx,0,0);items[0].body_id={"moving",6};items[0].dof_mask=7;
    items[0].reference_point=point(7,-11);items[0].dof_anchor=point(0.5,0.5);
    if(corner) {items[1].body=box(ctx,1,1);items[1].body_id={"fixed",5};items[1].boundary_type=EAB2_FIXED_BODY;}
    auto input=init<eab2_assembly2_input>(); input.flags=complete ? EAB2_ASSEMBLY_COMPLETE|EAB2_ASSEMBLY_EXPLICIT_PAIRS : 0;
    input.profile=EAB2_PROFILE1;input.body_count=corner?2:1;input.body_stride=sizeof(items[0]);input.bodies=items.data();
    eab2_pair2 pair{0,1}; input.pair_stride=sizeof(pair);
    if(corner){input.pair_count=1;input.pairs=&pair;} eab2_assembly2 assembly{};
    check(eab2_assembly2_create(ctx,&input,&assembly)==0,"assembly create");
    for(size_t i=0;i<input.body_count;++i) check(eab2_body2_destroy(ctx,items[i].body)==0,"body snapshot owns bytes");
    eab2_contact_set2 contacts{};check(eab2_assemble_contact_set2(ctx,assembly,&contacts)==0,"contacts create");
    check(eab2_assembly2_destroy(ctx,assembly)==0,"contacts own assembly"); return contacts;
}
std::string take(eab2_context ctx,eab2_exact_result& out) {
    check(out.call_status==0 && out.data && out.byte_count,"owned exact payload");
    const std::string s(out.data,static_cast<size_t>(out.byte_count));
    check(eab2_result_destroy(ctx,out.result)==0,"result release");
    check(eab2_result_destroy(ctx,out.result)==EAB2_INVALID_HANDLE,"stale result release");return s;
}
void contract() {
    auto abi=init<eab2_c3l3_abi_info>();check(eab2_get_c3l3_abi_info(&abi)==0,"ABI descriptor");
    check(abi.body_load2_size==sizeof(eab2_body_load2) && abi.limit2_input_size==sizeof(eab2_limit2_input)
        && abi.critical_parameter_input_size==sizeof(eab2_critical_parameter_input),"ABI sizes");
    abi.reserved=1;check(eab2_get_c3l3_abi_info(&abi)==EAB2_INVALID_INPUT,"ABI reserved");
    abi.reserved=0;abi.abi_version=2;check(eab2_get_c3l3_abi_info(&abi)==EAB2_UNSUPPORTED,"ABI version");
    auto info=init<eab2_abi_info>();info.requested_capabilities=EAB2_CAP_LIMIT2|EAB2_CAP_CRITICAL_PARAMETER;
    check(eab2_get_abi_info(&info)==0 && (info.supported_capabilities & info.requested_capabilities)==info.requested_capabilities,"production L3 capabilities");
    const auto ctx=context(),other=context(),contacts=isolated(ctx);
    eab2_body_load2 load{};load.live_bits[1]=bits(-1);
    auto input=init<eab2_limit2_input>(); input.body_count=1;input.body_stride=sizeof(load);input.loads=&load;
    auto critical=init<eab2_critical_parameter_input>();critical.mu_max_bits=bits(1);critical.max_steps=64;
    critical.body_count=1;critical.body_stride=sizeof(load);critical.loads=&load;critical.parameter=EAB2_PARAMETER_MU;
    auto out=init<eab2_exact_result>();
    check(eab2_solve_limit2(ctx,contacts,&input,&out)==0 && out.mathematical_status==EAB2_MATH_VALUE,"free live body has exact zero capacity");
    auto json=take(ctx,out);check(json.find("\"exact_value\":\"0/1\"")!=std::string::npos,"finite exact value");
    out=init<eab2_exact_result>();check(eab2_critical_parameter(ctx,contacts,&critical,&out)==0,"critical bounded domain");
    check(take(ctx,out).find("bounded_on_domain")!=std::string::npos,"bounded domain reason");
    load.dead_bits[1]=bits(-1);out=init<eab2_exact_result>();
    check(eab2_solve_limit2(ctx,contacts,&input,&out)==0 && out.mathematical_status==EAB2_MATH_INFEASIBLE,"Farkas call status separated");
    check(take(ctx,out).find("farkas")!=std::string::npos,"Farkas payload");
    out=init<eab2_exact_result>();check(eab2_critical_parameter(ctx,contacts,&critical,&out)==0 && out.mathematical_status==EAB2_MATH_INFEASIBLE,"critical infeasible not false finite");
    check(take(ctx,out).find("infeasible_on_domain")!=std::string::npos,"infeasible domain reason");
    load={};out=init<eab2_exact_result>();
    check(eab2_solve_limit2(ctx,contacts,&input,&out)==0 && out.mathematical_status==EAB2_MATH_UNBOUNDED,"zero live objective unbounded");
    json=take(ctx,out);check(json.find("feasible_point")!=std::string::npos && json.find("improving_ray")!=std::string::npos,"both unbounded witnesses");
    out=init<eab2_exact_result>();check(eab2_critical_parameter(ctx,contacts,&critical,&out)==0 && out.mathematical_status==EAB2_MATH_VALUE,"critical zero threshold");
    check(take(ctx,out).find("\"attained\":true")!=std::string::npos,"zero attained");
    for(unsigned k=0;k<10;++k) {
        auto bad=input;auto bad_load=load;uint32_t expected=EAB2_INVALID_INPUT;
        if(k==0)--bad.struct_size;
        if(k==1){bad.abi_version=2;expected=EAB2_UNSUPPORTED;}
        if(k==2)bad.mu_bits=bits(-1);
        if(k==3)bad.mu_bits=UINT64_C(0x7ff0000000000000);
        if(k==4)bad.mu_bits=UINT64_C(0x7ff8000000000001);
        if(k==5)bad.body_count=0;
        if(k==6)bad.body_stride=1;
        if(k==7)bad.body_count=UINT64_MAX;
        if(k==8)bad.loads=nullptr;
        if(k==9){bad_load.dead_bits[2]=UINT64_C(0x7ff0000000000000);bad.loads=&bad_load;}
        out=init<eab2_exact_result>();const auto before=out;
        check(eab2_solve_limit2(ctx,contacts,&bad,&out)==expected && std::memcmp(&before,&out,sizeof(out))==0,"invalid limit atomic output");
        if(k==9){auto err=init<eab2_error_info>();uint64_t n=0;check(eab2_context_get_error(ctx,&err,nullptr,0,&n)==0 && err.index==0 && std::string(err.field)=="loads","load error field and index");}
    }
    for(unsigned k=0;k<12;++k) {
        auto bad=critical;uint32_t expected=EAB2_INVALID_INPUT;
        if(k==0)--bad.struct_size;
        if(k==1){bad.abi_version=2;expected=EAB2_UNSUPPORTED;}
        if(k==2)bad.mu_max_bits=bits(-1);
        if(k==3)bad.mu_max_bits=UINT64_C(0x7ff0000000000000);
        if(k==4)bad.mu_max_bits=UINT64_C(0x7ff8000000000001);
        if(k==5)bad.body_count=0;
        if(k==6)bad.body_stride=1;
        if(k==7)bad.body_count=UINT64_MAX;
        if(k==8)bad.loads=nullptr;
        if(k==9)bad.reserved=1;
        if(k==10){bad.parameter=2;expected=EAB2_UNSUPPORTED;}
        if(k==11){bad.max_steps=4097;expected=EAB2_RESOURCE_LIMIT;}
        out=init<eab2_exact_result>();const auto before=out;
        check(eab2_critical_parameter(ctx,contacts,&bad,&out)==expected && std::memcmp(&before,&out,sizeof(out))==0,"invalid critical atomic output");
    }
    out=init<eab2_exact_result>();const auto before=out;
    check(eab2_solve_limit2(ctx,contacts,nullptr,&out)==EAB2_INVALID_INPUT && std::memcmp(&before,&out,sizeof(out))==0,"null limit input");
    check(eab2_critical_parameter(ctx,contacts,nullptr,&out)==EAB2_INVALID_INPUT && std::memcmp(&before,&out,sizeof(out))==0,"null critical input");
    check(eab2_solve_limit2(ctx,contacts,&input,nullptr)==EAB2_INVALID_INPUT,"null limit output");
    check(eab2_critical_parameter(ctx,contacts,&critical,nullptr)==EAB2_INVALID_INPUT,"null critical output");
    check(eab2_solve_limit2(other,contacts,&input,&out)==EAB2_INVALID_HANDLE && std::memcmp(&before,&out,sizeof(out))==0,"foreign limit handle");
    check(eab2_critical_parameter(other,contacts,&critical,&out)==EAB2_INVALID_HANDLE,"foreign critical handle");
    check(eab2_solve_limit2(ctx,ctx,&input,&out)==EAB2_INVALID_HANDLE,"wrong typed handle");
    const std::array<unsigned,11> modes{0x8000,0x0040,0x2000,0x4000,0x6000,7,8,9,10,11,12};
    for(const auto mode:modes) {
        const auto saved=_mm_getcsr();const auto bad=mode>=7 && mode<=12?((saved&~0x3fU)&~(1U<<mode)):(saved|mode);
        _mm_setcsr(bad);const auto s=eab2_solve_limit2(ctx,contacts,&input,&out);
        const auto c=eab2_critical_parameter(ctx,contacts,&critical,&out);const auto after=_mm_getcsr();_mm_setcsr(saved);
        check(s==EAB2_FP_CONTRACT && c==EAB2_FP_CONTRACT && after==bad && std::memcmp(&before,&out,sizeof(out))==0,"L3 FP guards preserve environment/output");
    }
    check(eab2_contact_set2_destroy(ctx,contacts)==0,"contact release");
    check(eab2_solve_limit2(ctx,contacts,&input,&out)==EAB2_INVALID_HANDLE,"stale limit handle");
    check(eab2_critical_parameter(ctx,contacts,&critical,&out)==EAB2_INVALID_HANDLE,"stale critical handle");
    check(eab2_context_destroy(ctx)==0 && eab2_context_destroy(other)==0,"cleanup");
}
void unresolved() {
    const auto ctx=context();
    for(unsigned k=0;k<2;++k) {
        const auto contacts=isolated(ctx,k!=0,k==1);std::array<eab2_body_load2,2> loads{};
        auto input=init<eab2_limit2_input>();input.body_count=k==1?2:1;input.body_stride=sizeof(loads[0]);input.loads=loads.data();
        auto out=init<eab2_exact_result>();
        check(eab2_solve_limit2(ctx,contacts,&input,&out)==0 && out.mathematical_status==(k?EAB2_MATH_MECHANICAL_UNRESOLVED:EAB2_MATH_UNPROVED),"honest unresolved status");
        check(take(ctx,out).find(k?"contact_set_unresolved":"completeness_unknown")!=std::string::npos,"honest unresolved reason");
        check(eab2_contact_set2_destroy(ctx,contacts)==0,"unresolved cleanup");
    }
    check(eab2_context_destroy(ctx)==0,"unresolved context cleanup");
}
void resource_limit() {
    const auto ctx=context();auto limits=init<eab2_context_limits2>();
    check(eab2_context_get_limits2(ctx,&limits)==0,"get resource limits");
    limits.max_integer_bits=128;
    check(eab2_context_configure_limits2(ctx,&limits)==0,"configure finite integer budget");
    const auto contacts=isolated(ctx);eab2_body_load2 load{};
    auto input=init<eab2_limit2_input>();input.body_count=1;input.body_stride=sizeof(load);input.loads=&load;
    input.mu_bits=UINT64_C(1823)<<52; // 2^800, finite binary64 but above this context budget.
    auto out=init<eab2_exact_result>();const auto before=out;
    check(eab2_solve_limit2(ctx,contacts,&input,&out)==EAB2_RESOURCE_LIMIT && std::memcmp(&before,&out,sizeof(out))==0,"integer budget failure has no mathematical output");
    auto request=init<eab2_critical_parameter_input>();request.body_count=1;request.body_stride=sizeof(load);
    request.loads=&load;request.parameter=1;request.max_steps=64;request.mu_max_bits=input.mu_bits;
    check(eab2_critical_parameter(ctx,contacts,&request,&out)==EAB2_RESOURCE_LIMIT && std::memcmp(&before,&out,sizeof(out))==0,"critical integer budget failure atomic");
    input.mu_bits=0;check(eab2_solve_limit2(ctx,contacts,&input,&out)==0,"context reusable after resource refusal");take(ctx,out);
    check(eab2_context_destroy(ctx)==0,"budget cleanup");
}
}
int main(){try{contract();unresolved();resource_limit();std::cout<<"EAB2_C3L3_ABI checks="<<checks<<" failed=0\n";return 0;}
    catch(const std::exception& e){std::cerr<<"EAB2_C3L3_ABI failed="<<e.what()<<" after="<<checks<<"\n";return 1;}}
