#include "eab2/c_api.h"
#include "eab2/testing.h"

#include <cfenv>
#include <cstdint>
#include <cstring>
#include <float.h>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#include <xmmintrin.h>

namespace {
uint64_t assertions = 0;
void check(bool condition, const char* name) {
    ++assertions;
    if (!condition) throw std::runtime_error(name);
}
template<class T> T initialized() {
    T result{};
    result.struct_size = sizeof(T);
    result.abi_version = EAB2_ABI_VERSION;
    return result;
}
bool is_null(const eab2_context& value) {
    return !value.owner && !value.id && !value.generation && !value.type && !value.reserved;
}
struct Batch {
    std::string source = "3ff0000000000000";
    eab2_text text{source.data(), source.size()};
    eab2_numeric_input item = initialized<eab2_numeric_input>();
    uint64_t bits = UINT64_C(0xdeadbeefcafef00d);
    eab2_numeric_output result = initialized<eab2_numeric_output>();
    eab2_numeric_batch_input input = initialized<eab2_numeric_batch_input>();
    eab2_numeric_batch_output output = initialized<eab2_numeric_batch_output>();
    Batch() {
        item.operation = EAB2_OP_SCALAR;
        item.encoding = EAB2_ENCODING_BITS;
        item.value_count = 1;
        item.value_stride = sizeof(eab2_text);
        item.values = &text;
        result.bits_capacity = 1;
        result.bits = &bits;
        result.bits_count = 77;
        input.item_count = 1;
        input.item_stride = sizeof(eab2_numeric_input);
        input.items = &item;
        output.item_capacity = 1;
        output.item_stride = sizeof(eab2_numeric_output);
        output.item_count = 99;
        output.items = &result;
    }
    void replace(std::string value) {
        source = std::move(value);
        text = {source.data(), source.size()};
    }
    uint32_t run(eab2_context context) { return eab2_numeric_batch(context, &input, &output); }
};
struct HostState {
    fenv_t environment{};
    unsigned mxcsr = _mm_getcsr();
    HostState() { std::fegetenv(&environment); }
    ~HostState() { std::fesetenv(&environment); _mm_setcsr(mxcsr); }
};
unsigned control_word() {
    unsigned value = 0;
    _controlfp_s(&value, 0, 0);
    return value;
}
void check_bad_environment(eab2_context context, const char* name) {
    const unsigned before = _mm_getcsr(), control = control_word();
    check(eab2_self_test() == EAB2_FP_CONTRACT, name);
    check(_mm_getcsr() == before && control_word() == control, "self_test preserves bad host state");
    auto options = initialized<eab2_context_options>();
    eab2_context failed{17, 18, 19, 20, 21};
    check(eab2_context_create(&options, &failed) == EAB2_FP_CONTRACT, "create rejects bad environment");
    check(is_null(failed), "failed create clears full handle");
    check(_mm_getcsr() == before && control_word() == control, "create preserves bad host state");
    Batch batch;
    check(batch.run(context) == EAB2_FP_CONTRACT, "batch rechecks calling thread environment");
    check(batch.output.item_count == 99 && batch.result.bits_count == 77 &&
          batch.bits == UINT64_C(0xdeadbeefcafef00d), "bad environment leaves output untouched");
    check(_mm_getcsr() == before && control_word() == control, "batch preserves bad host state");
}
void environment_matrix(eab2_context context) {
    for (unsigned mode : {0x8000U, 0x0040U}) {
        HostState saved;
        _mm_setcsr(saved.mxcsr | mode);
        check_bad_environment(context, mode == 0x8000U ? "FTZ rejected" : "DAZ rejected");
    }
    for (int mode : {FE_DOWNWARD, FE_UPWARD, FE_TOWARDZERO}) {
        HostState saved;
        check(std::fesetround(mode) == 0, "harness changes rounding");
        check_bad_environment(context, "non-nearest rounding rejected");
    }
    for (unsigned bit = 7; bit <= 12; ++bit) {
        HostState saved;
        // Clear pending flags before unmasking, then do no floating arithmetic.
        _mm_setcsr((saved.mxcsr & ~0x3fU) & ~(1U << bit));
        check_bad_environment(context, "unmasked exception rejected before probes");
    }
    const auto before = _mm_getcsr(), control = control_word();
    check(eab2_self_test() == EAB2_OK, "valid environment accepted");
    check(_mm_getcsr() == before && control_word() == control, "valid probes preserve full host state");
    {
        HostState saved;
        _mm_setcsr(saved.mxcsr | 0x3fU);
        const auto sticky = _mm_getcsr();
        check(eab2_self_test() == EAB2_OK && _mm_getcsr() == sticky,
              "valid probes preserve preexisting sticky exception flags");
    }
    std::cout << "FP_ENVIRONMENT: FTZ=reject DAZ=reject ROUND_MODES=3_reject MASK_BITS_7_12=6_reject HOST_STATE=unchanged\n";
}
void structural_matrix(eab2_context context) {
    for (int test = 0; test != 14; ++test) {
        Batch batch;
        switch (test) {
        case 0: --batch.input.struct_size; break;
        case 1: --batch.output.struct_size; break;
        case 2: --batch.input.item_stride; break;
        case 3: --batch.output.item_stride; break;
        case 4: batch.output.item_capacity = 0; break;
        case 5: batch.input.item_count = UINT64_MAX; break;
        case 6: batch.output.item_capacity = UINT64_MAX; break;
        case 7: --batch.item.value_stride; break;
        case 8: batch.item.value_count = UINT64_MAX; break;
        case 9: batch.result.bits_capacity = UINT64_MAX; break;
        case 10: batch.item.flags = 2; break;
        case 11: batch.item.values = nullptr; break;
        case 12: batch.result.bits = nullptr; break;
        case 13: batch.item.reserved = 1; break;
        }
        check(batch.run(context) == EAB2_INVALID_INPUT, "invalid descriptor rejected");
        check(batch.output.item_count == 99 && batch.result.bits_count == 77 &&
              batch.bits == UINT64_C(0xdeadbeefcafef00d), "structural failure has no partial output");
    }
    Batch bad_version;
    ++bad_version.input.abi_version;
    check(bad_version.run(context) == EAB2_UNSUPPORTED, "unsupported batch version rejected");
    Batch bad_item_version;
    ++bad_item_version.item.abi_version;
    check(bad_item_version.run(context) == EAB2_UNSUPPORTED, "unsupported item input version rejected");
    Batch bad_result_version;
    ++bad_result_version.result.abi_version;
    check(bad_result_version.run(context) == EAB2_UNSUPPORTED, "unsupported item output version rejected");
    Batch empty;
    empty.input.item_count = 0;
    empty.input.items = nullptr;
    empty.output.item_capacity = 0;
    empty.output.items = nullptr;
    check(empty.run(context) == EAB2_OK && empty.output.item_count == 0, "empty batch explicitly accepted");
    Batch resource;
    resource.text.length = 1048577;
    check(resource.run(context) == EAB2_RESOURCE_LIMIT, "deterministic text resource limit");
}
void numeric_status_matrix(eab2_context context) {
    for (const char* invalid : {"7ff0000000000000", "fff0000000000000", "7ff8000000000000",
                                "3FF0000000000000", "3ff000000000000", "03ff0000000000000"}) {
        Batch batch;
        batch.replace(invalid);
        check(batch.run(context) == EAB2_OK, "per-item input failure is not structural batch failure");
        check(batch.result.call_status == EAB2_INVALID_INPUT &&
              batch.result.mathematical_status == EAB2_MATH_NOT_COMPUTED &&
              batch.result.display_status == EAB2_DISPLAY_NOT_AVAILABLE &&
              batch.result.bits_count == 0 && batch.bits == UINT64_C(0xdeadbeefcafef00d),
              "invalid input has no false mathematical result or zero placeholder");
    }
    Batch unknown;
    unknown.item.operation = UINT32_MAX;
    check(unknown.run(context) == EAB2_OK && unknown.result.call_status == EAB2_UNSUPPORTED &&
          unknown.result.bits_count == 0, "unknown numeric capability explicitly unsupported");
    Batch capacity;
    capacity.result.bits_capacity = 0;
    check(capacity.run(context) == EAB2_OK && capacity.result.call_status == EAB2_INVALID_INPUT &&
          capacity.result.bits_count == 0, "insufficient numeric output capacity rejected");
    Batch range;
    range.item.encoding = EAB2_ENCODING_RATIONAL;
    range.replace("1/1" + std::string(400, '0'));
    check(range.run(context) == EAB2_OK && range.result.call_status == EAB2_CONSTRUCTION_RANGE &&
          range.result.mathematical_status == EAB2_MATH_NOT_COMPUTED &&
          range.result.display_status == EAB2_DISPLAY_RANGE && range.result.bits_count == 0 &&
          range.bits == UINT64_C(0xdeadbeefcafef00d), "range failure is explicit with invalid untouched bits");
    range.item.flags = EAB2_NUMERIC_ALLOW_UNDERFLOW;
    check(range.run(context) == EAB2_OK && range.result.call_status == EAB2_OK &&
          range.result.bits_count == 1 && range.bits == 0 &&
          range.result.display_status == EAB2_DISPLAY_UNDERFLOW_ZERO, "explicit underflow opt-in is separately reported");
    Batch exact;
    check(exact.run(context) == EAB2_OK && exact.result.call_status == EAB2_OK &&
          exact.result.mathematical_status == EAB2_MATH_VALUE && exact.result.display_status == EAB2_DISPLAY_VALID &&
          exact.result.bits_count == 1 && exact.bits == UINT64_C(0x3ff0000000000000), "scalar bits roundtrip");
    // Two items commit independently only after full descriptor validation.
    Batch valid, invalid;
    invalid.item.operation = UINT32_MAX;
    eab2_numeric_input inputs[] = {valid.item, invalid.item};
    eab2_numeric_output outputs[] = {valid.result, invalid.result};
    auto input = valid.input;
    input.item_count = 2;
    input.items = inputs;
    auto output = valid.output;
    output.item_capacity = 2;
    output.items = outputs;
    --inputs[1].value_stride;
    check(eab2_numeric_batch(context, &input, &output) == EAB2_INVALID_INPUT &&
          valid.bits == UINT64_C(0xdeadbeefcafef00d) && invalid.bits == UINT64_C(0xdeadbeefcafef00d) &&
          outputs[0].bits_count == 77 && outputs[1].bits_count == 77,
          "later invalid descriptor prevents earlier item from committing");
    ++inputs[1].value_stride;
    check(eab2_numeric_batch(context, &input, &output) == EAB2_OK && output.item_count == 2,
          "partial batch completion protocol");
    check(outputs[0].call_status == EAB2_OK && outputs[1].call_status == EAB2_UNSUPPORTED &&
          valid.bits == UINT64_C(0x3ff0000000000000) && invalid.bits == UINT64_C(0xdeadbeefcafef00d),
          "partial batch leaves failed buffer intact");
    auto error = initialized<eab2_error_info>();
    uint64_t required = 0;
    check(eab2_context_get_error(context, &error, nullptr, 0, &required) == EAB2_OK &&
          error.code == EAB2_UNSUPPORTED && error.index == 1 && required > 1, "context error size query and item index");
    char tiny = '!';
    check(eab2_context_get_error(context, &error, &tiny, 1, &required) == EAB2_INVALID_INPUT && tiny == '!',
          "short error buffer untouched");
    std::vector<char> message(static_cast<size_t>(required));
    check(eab2_context_get_error(context, &error, message.data(), message.size(), &required) == EAB2_OK &&
          std::strcmp(error.field, "numeric") == 0 && message.back() == '\0', "error copy and ownership");
    check(exact.run(context) == EAB2_OK, "subsequent successful batch");
    check(eab2_context_get_error(context, &error, nullptr, 0, &required) == EAB2_OK &&
          error.code == EAB2_OK && required == 1, "error lifecycle ends on next successful batch");
    check(EAB2_MATH_UNPROVED != EAB2_MATH_VALUE && EAB2_MATH_UNPROVED != EAB2_MATH_NOT_COMPUTED,
          "UNPROVED has distinct mathematical status representation");
}
void geometry2_matrix(eab2_context context, eab2_context other) {
    auto info = initialized<eab2_c1_abi_info>();
    check(eab2_get_c1_abi_info(&info) == EAB2_OK && info.query2_item_size == sizeof(eab2_query2_item) &&
          info.exact_result_size == sizeof(eab2_exact_result), "C1 ABI size discovery");
    const eab2_point2_bits square[] = {{0,0}, {UINT64_C(0x3ff0000000000000),0},
        {UINT64_C(0x3ff0000000000000),UINT64_C(0x3ff0000000000000)}, {0,UINT64_C(0x3ff0000000000000)}};
    auto input = initialized<eab2_body2_input>();
    input.vertex_count = 4; input.vertex_stride = sizeof(eab2_point2_bits); input.vertices = square;
    eab2_body2 a{}, b{}, recycled{};
    check(eab2_body2_create(context, &input, &a) == EAB2_OK, "first body created");
    check(eab2_body2_create(context, &input, &b) == EAB2_OK, "second body created");
    check(eab2_body2_destroy(other, a) == EAB2_INVALID_HANDLE, "cross-context body rejected");
    auto options = initialized<eab2_entrance2_options>();
    eab2_entrance2 entrance{};
    check(eab2_entrance2_create(context, a, b, &options, &entrance) == EAB2_OK, "entrance created");
    check(eab2_body2_destroy(context, entrance) == EAB2_INVALID_HANDLE, "wrong child type rejected");
    check(eab2_body2_destroy(context, a) == EAB2_OK, "body independent of entrance copy");
    check(eab2_body2_create(context, &input, &recycled) == EAB2_OK && recycled.id == a.id &&
          recycled.generation > a.generation, "body slot reuse advances generation");
    check(eab2_body2_destroy(context, a) == EAB2_INVALID_HANDLE, "old body rejected after reuse");
    auto invalid = input; --invalid.vertex_stride;
    auto failed = b;
    check(eab2_body2_create(context, &invalid, &failed) == EAB2_INVALID_INPUT && is_null(failed),
          "body stride failure leaves null token");
    invalid = input; invalid.vertex_count = UINT64_MAX;
    check(eab2_body2_create(context, &invalid, &failed) == EAB2_INVALID_INPUT && is_null(failed), "body extent overflow rejected");
    auto query = initialized<eab2_query2_input>();
    const eab2_point2_bits points[] = {{0,0}, {UINT64_C(0x3ff0000000000000),0},
        {UINT64_C(0x4000000000000000),0}, {UINT64_C(0x7ff0000000000000),0}};
    query.point_count = 4; query.point_stride = sizeof(eab2_point2_bits); query.points = points;
    eab2_query2_item items[4]{};
    auto output = initialized<eab2_query2_output>();
    output.item_capacity = 4; output.item_stride = sizeof(eab2_query2_item); output.items = items;
    check(eab2_query2_batch(context, entrance, &query, &output) == EAB2_OK && output.item_count == 4,
          "geometry batch partial success");
    check(items[0].body_state == EAB2_BODY_OVERLAP && items[0].topology_state == EAB2_TOPOLOGY_INTERIOR,
          "overlap not invocation error");
    check(items[1].body_state == EAB2_BODY_CONTACT && items[1].topology_state == EAB2_TOPOLOGY_BOUNDARY,
          "contact and boundary are separate states");
    check(items[2].body_state == EAB2_BODY_OUTSIDE && items[2].topology_state == EAB2_TOPOLOGY_OUTSIDE,
          "outside query");
    check(items[3].call_status == EAB2_INVALID_INPUT && items[3].mathematical_status == EAB2_MATH_NOT_COMPUTED &&
          items[3].body_state == UINT32_MAX, "nonfinite query not a false outside result");
    --query.point_stride; output.item_count = 99; items[0].body_state = 99;
    check(eab2_query2_batch(context, entrance, &query, &output) == EAB2_INVALID_INPUT &&
          output.item_count == 99 && items[0].body_state == 99, "geometry structural failure atomic");
    ++query.point_stride;
    for (int test = 0; test != 9; ++test) {
        auto bad_query = query;
        auto bad_output = output;
        bad_output.item_count = 99; items[0].body_state = 99;
        if (test == 0) --bad_query.struct_size;
        if (test == 1) --bad_output.struct_size;
        if (test == 2) --bad_output.item_stride;
        if (test == 3) bad_output.item_capacity = 3;
        if (test == 4) bad_query.point_count = UINT64_MAX;
        if (test == 5) bad_output.item_capacity = UINT64_MAX;
        if (test == 6) bad_query.points = nullptr;
        if (test == 7) bad_output.items = nullptr;
        if (test == 8) ++bad_query.abi_version;
        check(eab2_query2_batch(context, entrance, &bad_query, &bad_output) ==
              (test == 8 ? EAB2_UNSUPPORTED : EAB2_INVALID_INPUT) && bad_output.item_count == 99 &&
              items[0].body_state == 99, "C1 query structural matrix atomic");
    }
    check(eab2_membership2_batch(context, entrance, &query, &output) == EAB2_OK &&
          eab2_topology2_batch(context, entrance, &query, &output) == EAB2_OK, "membership topology entry families");
    auto exact = initialized<eab2_exact_result>();
    check(eab2_result_export_exact(context, entrance, &exact) == EAB2_OK && exact.byte_count && exact.data &&
          std::strstr(exact.data, "eab2.c1.exact.v1"), "exact export library allocation");
    const auto old_result = exact.result;
    check(eab2_result_destroy(other, exact.result) == EAB2_INVALID_HANDLE, "result owner validated");
    check(eab2_result_destroy(context, exact.result) == EAB2_OK, "result freed by library");
    exact = initialized<eab2_exact_result>();
    check(eab2_local_origin2_exact(context, entrance, &exact) == EAB2_OK && exact.byte_count &&
          exact.result.id == old_result.id && exact.result.generation > old_result.generation,
          "local exact result and slot reuse");
    check(eab2_result_destroy(context, old_result) == EAB2_INVALID_HANDLE, "stale result rejected after reuse");
    check(eab2_result_destroy(context, exact.result) == EAB2_OK, "local result released");
    eab2_point2_exact rational{{"1/3",3},{"0/1",3}};
    auto rational_query = initialized<eab2_query2_exact_input>();
    rational_query.point_count = 1; rational_query.point_stride = sizeof(eab2_point2_exact); rational_query.points = &rational;
    check(eab2_query2_exact_batch(context, entrance, &rational_query, &output) == EAB2_OK &&
          items[0].body_state == EAB2_BODY_OVERLAP, "test rational query without rounding");
    check(eab2_entrance2_destroy(context, entrance) == EAB2_OK, "entrance released");
    check(eab2_query2_batch(context, entrance, &query, &output) == EAB2_INVALID_HANDLE, "stale entrance rejected");

    options.flags = EAB2_ENTRANCE_NO_CACHE;
    eab2_entrance2 uncached{};
    check(eab2_entrance2_create(context, b, recycled, &options, &uncached) == EAB2_OK,
          "cache-off option accepted independently of merge/compact");
    exact = initialized<eab2_exact_result>();
    check(eab2_result_export_exact(context, uncached, &exact) == EAB2_OK, "uncached first global export");
    const std::string first_export(exact.data, static_cast<size_t>(exact.byte_count));
    check(eab2_result_destroy(context, exact.result) == EAB2_OK, "uncached first result released");
    exact = initialized<eab2_exact_result>();
    check(eab2_result_export_exact(context, uncached, &exact) == EAB2_OK &&
          first_export == std::string(exact.data, static_cast<size_t>(exact.byte_count)), "uncached exports semantic equality");
    check(eab2_result_destroy(context, exact.result) == EAB2_OK, "uncached second result released");
    exact = initialized<eab2_exact_result>();
    check(eab2_local_origin2_exact(context, uncached, &exact) == EAB2_OK &&
          std::strstr(exact.data, "\"global_subdivision_materialized\":false"),
          "cache-off discards global cache before next local query");
    check(eab2_result_destroy(context, exact.result) == EAB2_OK, "uncached local result released");
    check(eab2_query2_batch(context, uncached, &query, &output) == EAB2_OK &&
          items[1].body_state == EAB2_BODY_CONTACT, "cache-off membership semantics retained");
    check(eab2_entrance2_destroy(context, uncached) == EAB2_OK, "uncached entrance released");
    options.flags = 8;
    check(eab2_entrance2_create(context, b, recycled, &options, &uncached) == EAB2_INVALID_INPUT && is_null(uncached),
          "unsupported entrance option rejected with null token");
    check(eab2_body2_destroy(context, b) == EAB2_OK && eab2_body2_destroy(context, recycled) == EAB2_OK, "body cleanup");
    Batch work;
    work.item.encoding = EAB2_ENCODING_RATIONAL;
    work.replace("1/" + std::string(4096, '9'));
    check(work.run(context) == EAB2_OK && work.result.call_status == EAB2_RESOURCE_LIMIT &&
          work.result.mathematical_status == EAB2_MATH_NOT_COMPUTED, "decimal work budget not just bytes");
    Batch aggregate;
    aggregate.item.encoding = EAB2_ENCODING_RATIONAL;
    aggregate.replace("1/" + std::string(6000, '9'));
    eab2_text texts[] = {aggregate.text, aggregate.text};
    aggregate.item.value_count = 2; aggregate.item.values = texts;
    check(aggregate.run(context) == EAB2_RESOURCE_LIMIT && aggregate.output.item_count == 99 &&
          aggregate.bits == UINT64_C(0xdeadbeefcafef00d), "aggregate work budget rejected before parsing");
}
void child_context_reuse() {
    auto options = initialized<eab2_context_options>();
    eab2_context first{}, second{};
    check(eab2_context_create(&options, &first) == EAB2_OK, "child lifetime context");
    const eab2_point2_bits triangle[] = {{0,0}, {UINT64_C(0x3ff0000000000000),0}, {0,UINT64_C(0x3ff0000000000000)}};
    auto input = initialized<eab2_body2_input>();
    input.vertex_count = 3; input.vertex_stride = sizeof(eab2_point2_bits); input.vertices = triangle;
    eab2_body2 old_body{}, new_body{};
    check(eab2_body2_create(first, &input, &old_body) == EAB2_OK, "child before context release");
    check(eab2_context_destroy(first) == EAB2_OK, "context release frees owned child payload");
    check(eab2_context_create(&options, &second) == EAB2_OK && second.id == first.id,
          "context containing old child slot reused");
    check(eab2_body2_create(second, &input, &new_body) == EAB2_OK && new_body.id == old_body.id &&
          new_body.generation != old_body.generation, "child id reused across context generation");
    check(eab2_body2_destroy(second, old_body) == EAB2_INVALID_HANDLE,
          "old child cannot cross a reused context id");
    check(eab2_context_destroy(second) == EAB2_OK, "context RAII final child cleanup");
}

void limits2_matrix() {
    auto options = initialized<eab2_context_options>();
    eab2_context context{};
    check(eab2_context_create(&options, &context) == EAB2_OK, "limits context created");
    auto original = initialized<eab2_context_limits2>();
    check(eab2_context_get_limits2(context, &original) == EAB2_OK && original.max_work_units == 50000000 &&
          original.max_elements == 2000000 && original.max_integer_bits == 65536, "explicit actual default limits");
    auto configured = original;
    configured.max_work_units = 0;
    check(eab2_context_configure_limits2(context, &configured) == EAB2_INVALID_INPUT,
          "zero is rejected, not an undocumented default sentinel");
    const eab2_point2_bits triangle[] = {{0,0}, {UINT64_C(0x3ff0000000000000),0}, {0,UINT64_C(0x3ff0000000000000)}};
    auto input = initialized<eab2_body2_input>();
    input.vertex_count = 3; input.vertex_stride = sizeof(eab2_point2_bits); input.vertices = triangle;
    eab2_body2 body{};
    check(eab2_body2_create(context, &input, &body) == EAB2_OK, "body under default limits");
    check(eab2_context_configure_limits2(context, &original) == EAB2_INVALID_INPUT,
          "limits immutable while any child is live");
    check(eab2_body2_destroy(context, body) == EAB2_OK, "release before configuration");
    configured = original; configured.max_integer_bits = 8;
    check(eab2_context_configure_limits2(context, &configured) == EAB2_OK, "set conservative bit budget");
    auto observed = initialized<eab2_context_limits2>();
    check(eab2_context_get_limits2(context, &observed) == EAB2_OK && observed.max_integer_bits == 8,
          "configured limits exact readback");
    check(eab2_body2_create(context, &input, &body) == EAB2_RESOURCE_LIMIT && is_null(body),
          "bit budget throws resource status, not outside/invalid geometry");
    configured = original; configured.max_elements = 2;
    check(eab2_context_configure_limits2(context, &configured) == EAB2_OK, "set element budget");
    check(eab2_body2_create(context, &input, &body) == EAB2_RESOURCE_LIMIT && is_null(body), "input element limit enforced");
    configured = original; configured.max_work_units = 1;
    check(eab2_context_configure_limits2(context, &configured) == EAB2_OK, "set exact work budget");
    check(eab2_body2_create(context, &input, &body) == EAB2_RESOURCE_LIMIT && is_null(body), "body work limit enforced");
    check(eab2_context_configure_limits2(context, &original) == EAB2_OK &&
          eab2_body2_create(context, &input, &body) == EAB2_OK, "limits can restore only after failed/no live children");
    check(eab2_context_destroy(context) == EAB2_OK, "limited context cleanup");
}

}

int main() {
    try {
        auto info = initialized<eab2_abi_info>();
        check(eab2_get_abi_info(&info) == EAB2_OK, "ABI info available");
        info.reserved = 1;
        check(eab2_get_abi_info(&info) == EAB2_INVALID_INPUT, "ABI reserved input rejected");
        info.reserved = 0;
        check(info.context_size == sizeof(eab2_context) && info.pointer_bits == 64 &&
              info.binary64_bits == 64 && info.build_identity[0], "ABI sizes support domain identity");
        check(info.supported_capabilities == (EAB2_CAP_CONTEXT | EAB2_CAP_TEST_NUMERIC | EAB2_CAP_TEST_EXACT2 | EAB2_CAP_BODY2 | EAB2_CAP_ENTRANCE2 | EAB2_CAP_QUERY2 | EAB2_CAP_EXPORT_EXACT | EAB2_CAP_LOCAL2 | EAB2_CAP_LIMITS2), "test capabilities explicit");
        info.requested_capabilities = EAB2_CAP_RHO | EAB2_CAP_SE2 | EAB2_CAP_LP2;
        check(eab2_get_abi_info(&info) == EAB2_UNSUPPORTED &&
              info.unsupported_capabilities == info.requested_capabilities, "unimplemented capabilities unsupported");
        auto options = initialized<eab2_context_options>();
        eab2_context first{}, second{};
        check(eab2_context_create(&options, &first) == EAB2_OK, "first context creation");
        check(eab2_context_create(&options, &second) == EAB2_OK, "second context creation");
        auto invalid_options = options;
        invalid_options.flags = 1;
        eab2_context failed = first;
        check(eab2_context_create(&invalid_options, &failed) == EAB2_INVALID_INPUT && is_null(failed),
              "failed create no partial initialized handle");
        for (int test = 0; test != 5; ++test) {
            auto invalid = first;
            if (test == 0) invalid.owner = second.owner;
            if (test == 1) ++invalid.generation;
            if (test == 2) ++invalid.type;
            if (test == 3) invalid.reserved = 1;
            if (test == 4) invalid.id = 0;
            Batch batch;
            check(batch.run(invalid) == EAB2_INVALID_HANDLE, "cross-context/type/generation/null handle rejected");
            check(eab2_context_destroy(invalid) == EAB2_INVALID_HANDLE, "invalid destroy rejected without harming owner");
        }
        structural_matrix(first);
        numeric_status_matrix(first);
        environment_matrix(first);
        geometry2_matrix(first, second);
        check(eab2_context_destroy(first) == EAB2_OK, "library frees first context");
        check(eab2_context_destroy(first) == EAB2_INVALID_HANDLE, "double release rejected");
        Batch stale;
        check(stale.run(first) == EAB2_INVALID_HANDLE, "stale token rejected");
        auto error = initialized<eab2_error_info>();
        uint64_t required = 0;
        check(eab2_context_get_error(first, &error, nullptr, 0, &required) == EAB2_INVALID_HANDLE,
              "stale error context rejected");
        check(eab2_context_get_error(second, &error, nullptr, 0, &required) == EAB2_OK && error.code == EAB2_INVALID_HANDLE,
              "intentional cross-context errors remain context-local");
        check(eab2_context_destroy(second) == EAB2_OK, "library frees second context");
        eab2_context reused{};
        check(eab2_context_create(&options, &reused) == EAB2_OK, "context slot reused");
        check((reused.id == first.id || reused.id == second.id) && reused.generation > second.generation,
              "reused context slot advances generation");
        check(eab2_context_destroy(first) == EAB2_INVALID_HANDLE && eab2_context_destroy(second) == EAB2_INVALID_HANDLE,
              "both old context generations rejected after slot reuse");
        check(eab2_context_destroy(reused) == EAB2_OK, "release reused context");
        for (unsigned i = 0; i < 256; ++i) {
            eab2_context token{};
            check(eab2_context_create(&options, &token) == EAB2_OK && token.generation != first.generation, "generation-safe fresh ownership");
            check(eab2_context_destroy(token) == EAB2_OK && eab2_context_destroy(token) == EAB2_INVALID_HANDLE,
                  "repeated library ownership lifecycle");
        }
        child_context_reuse();
        limits2_matrix();
        std::cout << "ABI_TESTS: " << assertions << " assertions, 0 failures\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ABI_TESTS FAILED: " << error.what() << " (after " << assertions << " assertions)\n";
        return 1;
    }
}
