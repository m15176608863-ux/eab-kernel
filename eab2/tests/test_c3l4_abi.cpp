#include "eab2/c_api.h"
#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <xmmintrin.h>

namespace {
unsigned checks=0;
void check(bool value,const char* name){++checks;if(!value)throw std::runtime_error(name);}
template<class T>T init(){T out{};out.struct_size=sizeof(out);out.abi_version=1;return out;}
uint64_t bits(double x){return std::bit_cast<uint64_t>(x);}
eab2_string text(const char* p){return {p,static_cast<uint64_t>(std::strlen(p))};}
eab2_string_array strings(const std::vector<eab2_string>& v){return {v.size(),sizeof(eab2_string),v.data()};}
eab2_context context(){auto o=init<eab2_context_options>();eab2_context c{};check(eab2_context_create(&o,&c)==0,"context");return c;}
eab2_body2 box(eab2_context c,double y){
    const std::array<eab2_point2_bits,4> v{{{bits(0),bits(y)},{bits(1),bits(y)},{bits(1),bits(y+1)},{bits(0),bits(y+1)}}};
    auto in=init<eab2_body2_input>();in.vertex_count=v.size();in.vertex_stride=sizeof(v[0]);in.vertices=v.data();
    eab2_body2 out{};check(eab2_body2_create(c,&in,&out)==0,"body");return out;
}
eab2_contact_set2 contacts(eab2_context c){
    std::array<eab2_assembly_body2,2> b{init<eab2_assembly_body2>(),init<eab2_assembly_body2>()};
    b[0].body=box(c,-1);b[0].body_id=text("fixed");b[0].boundary_type=1;
    b[1].body=box(c,0);b[1].body_id=text("moving");b[1].dof_mask=3;
    for(auto& body:b){body.reference_point={bits(3),bits(-5)};body.dof_anchor={bits(-7),bits(11)};}
    auto in=init<eab2_assembly2_input>();in.flags=3;in.profile=1;in.body_count=2;in.body_stride=sizeof(b[0]);in.bodies=b.data();
    eab2_pair2 pair{0,1};in.pair_count=1;in.pair_stride=sizeof(pair);in.pairs=&pair;eab2_assembly2 a{};
    check(eab2_assembly2_create(c,&in,&a)==0,"assembly");
    for(const auto& body:b)check(eab2_body2_destroy(c,body.body)==0,"copied body");
    eab2_contact_set2 out{};check(eab2_assemble_contact_set2(c,a,&out)==0,"contacts");
    check(eab2_assembly2_destroy(c,a)==0,"copied assembly");return out;
}
struct Input {
    std::vector<eab2_string> ids{text("fixed"),text("moving")};
    std::vector<eab2_sensitivity_vertex2> vertex_ids;
    std::vector<eab2_string> vertices=std::vector<eab2_string>(48,text("0/1"));
    std::vector<eab2_string> dead=std::vector<eab2_string>(18,text("0/1"));
    std::vector<eab2_string> live=std::vector<eab2_string>(18,text("0/1"));
    std::vector<eab2_string> anchor=std::vector<eab2_string>(12,text("0/1"));
    std::vector<eab2_string> mu{text("1/1"),text("0/1"),text("0/1")};
    std::array<eab2_sensitivity_channel2,3> channels;
    eab2_sensitivity2_input value=init<eab2_sensitivity2_input>();
    Input(){
        for(auto id:ids)for(uint64_t i=0;i<4;++i)vertex_ids.push_back({id,i});
        const std::array<const char*,3> names{"mu","pressure","live"};
        for(size_t i=0;i<3;++i){channels[i]=init<eab2_sensitivity_channel2>();channels[i].parameter=text(names[i]);
            channels[i].positive_direction_valid=channels[i].negative_direction_valid=1;
            channels[i].validity_conditions.value_stride=channels[i].tied_labels.value_stride=sizeof(eab2_string);}
        dead[6+4]=text("-1/1");live[12+3]=text("1/1");
        value.parameter_count=value.channel_count=3;value.output_count=1;value.body_count=2;value.vertex_count=8;
        value.channel_stride=sizeof(channels[0]);value.channels=channels.data();value.body_ids=strings(ids);
        value.vertex_stride=sizeof(vertex_ids[0]);value.vertex_ids=vertex_ids.data();
        value.vertices=strings(vertices);value.dead=strings(dead);value.live=strings(live);value.dof_anchor=strings(anchor);value.mu=strings(mu);
    }
};
std::string take(eab2_context c,eab2_exact_result& out){
    check(out.call_status==0&&out.data&&out.byte_count,"owned result");std::string s(out.data,static_cast<size_t>(out.byte_count));
    check(eab2_result_destroy(c,out.result)==0,"result release");return s;
}
void parameter_budget_before_products(eab2_context c,eab2_result base){
    // The descriptor points only at the ordinary three-channel allocation.
    // Its claimed huge extent is representable; rejection must precede array
    // products, array-shape diagnostics, and any channel dereference.
    for(const uint64_t count:std::array<uint64_t,2>{1025,UINT64_C(1)<<56}){
        Input bad;bad.value.parameter_count=bad.value.channel_count=count;
        auto out=init<eab2_exact_result>();const auto before=out;
        check(eab2_evaluate_sensitivity2(c,base,&bad.value,&out)==EAB2_RESOURCE_LIMIT&&
            std::memcmp(&before,&out,sizeof(out))==0,"parameter_budget_before_products atomic rejection");
        auto error=init<eab2_error_info>();uint64_t required=0;
        check(eab2_context_get_error(c,&error,nullptr,0,&required)==0&&
            std::string(error.field)=="parameter_count"&&error.index==UINT64_MAX,
            "parameter_budget_before_products scalar named detail");
    }
    std::cout<<"PASS parameter_budget_before_products\n";
}
void contract(){
    auto info=init<eab2_c3l4_abi_info>();check(eab2_get_c3l4_abi_info(&info)==0,"size info");
    check(info.string_array_size==sizeof(eab2_string_array)&&info.sensitivity_vertex2_size==sizeof(eab2_sensitivity_vertex2)&&
        info.sensitivity_channel2_size==sizeof(eab2_sensitivity_channel2)&&info.sensitivity2_input_size==sizeof(eab2_sensitivity2_input),"all descriptor sizes");
    for(unsigned i=0;i<4;++i){auto bad=info;if(i==0)--bad.struct_size;if(i==1)bad.abi_version=2;if(i==2)bad.reserved=1;if(i==3)bad.reserved2=1;
        check(eab2_get_c3l4_abi_info(&bad)==(i==1?EAB2_UNSUPPORTED:EAB2_INVALID_INPUT),"ABI header rejection");}
    auto abi=init<eab2_abi_info>();abi.requested_capabilities=EAB2_CAP_SENSITIVITY2;
    check(eab2_get_abi_info(&abi)==0&&(abi.supported_capabilities&EAB2_CAP_SENSITIVITY2),"production sensitivity capability");
    check(!(abi.supported_capabilities&(EAB2_CAP_TEST_NUMERIC|EAB2_CAP_TEST_EXACT2|EAB2_CAP_TEST_OPT)),"production only");
    const auto c=context(),other=context(),contact=contacts(c);
    std::array<eab2_body_load2,2> loads{};loads[1].dead_bits[1]=bits(-2);loads[1].live_bits[0]=bits(1);
    auto limit=init<eab2_limit2_input>();limit.mu_bits=bits(0.25);limit.body_count=2;limit.body_stride=sizeof(loads[0]);limit.loads=loads.data();
    auto base=init<eab2_exact_result>();check(eab2_solve_limit2(c,contact,&limit,&base)==0,"retained L3 finite result");
    const std::string primal(base.data,static_cast<size_t>(base.byte_count));check(primal.find("\"exact_value\":\"1/2\"")!=std::string::npos,"finite base value");
    auto critical=init<eab2_critical_parameter_input>();critical.mu_max_bits=bits(1);critical.max_steps=8;critical.parameter=1;
    critical.body_count=2;critical.body_stride=sizeof(loads[0]);critical.loads=loads.data();auto cb=init<eab2_exact_result>();
    check(eab2_critical_parameter(c,contact,&critical,&cb)==0,"retained critical result");
    critical.mu_max_bits=UINT64_C(0x8000000000000000);auto signed_zero=init<eab2_exact_result>();
    check(eab2_critical_parameter(c,contact,&critical,&signed_zero)==0,"negative zero original search domain accepted");
    const auto signed_zero_json=take(c,signed_zero);
    check(signed_zero_json.find("\"mu_max_binary64\":\"8000000000000000\"")!=std::string::npos&&
        signed_zero_json.find("\"exact_mu_max\":\"0/1\"")!=std::string::npos,"original binary64 negative zero retained alongside exact domain zero");
    critical.mu_max_bits=bits(1);
    auto ordinary=init<eab2_exact_result>();check(eab2_contact_set2_export_exact(c,contact,&ordinary)==0,"ordinary result");
    check(eab2_contact_set2_destroy(c,contact)==0,"release contacts before sensitivity");
    parameter_budget_before_products(c,base.result);
    Input in;auto out=init<eab2_exact_result>();
    check(eab2_evaluate_sensitivity2(c,base.result,&in.value,&out)==0,"multiple channels after source destruction");
    auto json=take(c,out);check(json.find("\"jacobian\":[\"2/1\",\"1/4\",\"-1/2\"]")!=std::string::npos,"three distinct geometry/load seed derivatives");
    check(json.find("\"parameter_count\":3,\"output_count\":1,\"channel_count\":3")!=std::string::npos,"explicit dimensions");
    check(json.find("\"derived_seed\":{")!=std::string::npos,"derived seed exposed");
    out=init<eab2_exact_result>();check(eab2_evaluate_sensitivity2(c,cb.result,&in.value,&out)==EAB2_INVALID_INPUT,"critical rejects friction seed");
    auto detail=init<eab2_error_info>();uint64_t required=0;
    check(eab2_context_get_error(c,&detail,nullptr,0,&required)==0&&std::string(detail.field)=="mu"&&detail.index==0,"critical friction rejection field and channel");
    in.mu[0]=text("0/1");
    out=init<eab2_exact_result>();check(eab2_evaluate_sensitivity2(c,cb.result,&in.value,&out)==0,"uncertified critical stays honest");
    json=take(c,out);check(json.find("\"jacobian\":[null,null,null]")!=std::string::npos,"no forged critical slopes");
    for(unsigned i=0;i<35;++i){
        Input bad;auto expected=EAB2_INVALID_INPUT;
        if(i==0)--bad.value.struct_size;if(i==1){bad.value.abi_version=2;expected=EAB2_UNSUPPORTED;}
        if(i==2)bad.value.parameter_count=0;if(i==3)bad.value.output_count=2;if(i==4)bad.value.channel_count=2;
        if(i==5)bad.value.body_count=1;if(i==6)bad.value.vertex_count=7;if(i==7)bad.value.channel_stride=1;
        if(i==8)bad.value.channels=nullptr;if(i==9)bad.value.vertex_stride=1;if(i==10)bad.value.vertex_ids=nullptr;
        if(i==11)bad.value.vertices.value_count--;if(i==12)bad.value.dead.value_count--;if(i==13)bad.value.live.value_count--;
        if(i==14)bad.value.dof_anchor.value_count--;if(i==15)bad.value.mu.value_count--;if(i==16)bad.value.vertices.value_stride=1;
        if(i==17)bad.value.mu.values=nullptr;if(i==18)bad.ids[0]=text("moving");if(i==19)bad.vertex_ids[1]=bad.vertex_ids[0];
        if(i==20)bad.channels[0].positive_direction_valid=2;if(i==21)bad.channels[0].negative_direction_valid=2;
        if(i==22)bad.channels[1].parameter=bad.channels[0].parameter;if(i==23)bad.mu[0]=text("2/2");
        if(i==24)bad.channels[0].parameter=text("\xff");if(i==25)bad.channels[0].validity_conditions.value_stride=1;
        if(i==26)bad.channels[0].tied_labels.value_stride=1;if(i==27)bad.channels[0].struct_size--;
        if(i==28){bad.channels[0].abi_version=2;expected=EAB2_UNSUPPORTED;}if(i==29)bad.value.body_ids.value_count--;
        if(i==30)bad.value.body_ids.value_stride=1;if(i==31)bad.vertex_ids[0].vertex_id=UINT64_MAX;
        if(i==32){bad.value.parameter_count=bad.value.channel_count=UINT64_MAX;}
        if(i==33)bad.vertices[4]=text("1/1"); // A shared contact vertex must move consistently.
        if(i==34)bad.mu[0]={nullptr,1};
        out=init<eab2_exact_result>();const auto before=out;
        check(eab2_evaluate_sensitivity2(c,base.result,&bad.value,&out)==expected&&std::memcmp(&before,&out,sizeof(out))==0,"invalid input atomic result");
        if(i==23||i==24||i==33||i==34){
            detail=init<eab2_error_info>();
            check(eab2_context_get_error(c,&detail,nullptr,0,&required)==0&&std::string(detail.field)!="exception"&&detail.index!=UINT64_MAX,"sensitivity malformed text and seed retain named indexed detail");
        }
    }
    out=init<eab2_exact_result>();const auto before=out;
    check(eab2_evaluate_sensitivity2(c,base.result,nullptr,&out)==EAB2_INVALID_INPUT,"null input");
    check(eab2_evaluate_sensitivity2(c,base.result,&in.value,nullptr)==EAB2_INVALID_INPUT,"null output");
    check(eab2_evaluate_sensitivity2(other,base.result,&in.value,&out)==EAB2_INVALID_HANDLE,"foreign base");
    check(eab2_evaluate_sensitivity2(c,c,&in.value,&out)==EAB2_INVALID_HANDLE,"wrong type");
    check(eab2_evaluate_sensitivity2(c,ordinary.result,&in.value,&out)==EAB2_INVALID_HANDLE,"untyped JSON cannot be base");
    const std::array<unsigned,11> modes{0x8000,0x0040,0x2000,0x4000,0x6000,7,8,9,10,11,12};
    for(auto mode:modes){const auto saved=_mm_getcsr();const auto bad=mode>=7&&mode<=12?((saved&~0x3fU)&~(1U<<mode)):(saved|mode);
        _mm_setcsr(bad);const auto status=eab2_evaluate_sensitivity2(c,base.result,&in.value,&out);const auto after=_mm_getcsr();_mm_setcsr(saved);
        check(status==EAB2_FP_CONTRACT&&after==bad&&std::memcmp(&before,&out,sizeof(out))==0,"L4 FP guard no output/environment mutation");}
    check(eab2_result_destroy(c,base.result)==0,"base release");
    check(eab2_evaluate_sensitivity2(c,base.result,&in.value,&out)==EAB2_INVALID_HANDLE,"expired typed base");
    check(eab2_result_destroy(c,cb.result)==0&&eab2_result_destroy(c,ordinary.result)==0,"remaining release");
    check(eab2_context_destroy(c)==0&&eab2_context_destroy(other)==0,"contexts release");
}
}
int main(){try{contract();std::cout<<"EAB2_C3L4_ABI checks="<<checks<<" failed=0\n";return 0;}
catch(const std::exception& e){std::cerr<<"EAB2_C3L4_ABI failed="<<e.what()<<" after="<<checks<<"\n";return 1;}}
