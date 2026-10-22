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
          range.result.bits_count == 1 && range.bits == 0, "explicit underflow opt-in changes validity");
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
        check(info.supported_capabilities == (EAB2_CAP_CONTEXT | EAB2_CAP_TEST_NUMERIC), "test capabilities explicit");
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
        check(eab2_context_destroy(first) == EAB2_OK, "library frees first context");
        check(eab2_context_destroy(first) == EAB2_INVALID_HANDLE, "double release rejected");
        Batch stale;
        check(stale.run(first) == EAB2_INVALID_HANDLE, "stale token rejected");
        auto error = initialized<eab2_error_info>();
        uint64_t required = 0;
        check(eab2_context_get_error(first, &error, nullptr, 0, &required) == EAB2_INVALID_HANDLE,
              "stale error context rejected");
        check(eab2_context_get_error(second, &error, nullptr, 0, &required) == EAB2_OK && error.code == EAB2_OK,
              "errors are context-local, not global");
        check(eab2_context_destroy(second) == EAB2_OK, "library frees second context");
        for (unsigned i = 0; i < 256; ++i) {
            eab2_context token{};
            check(eab2_context_create(&options, &token) == EAB2_OK && token.id != first.id, "generation-safe fresh ownership");
            check(eab2_context_destroy(token) == EAB2_OK && eab2_context_destroy(token) == EAB2_INVALID_HANDLE,
                  "repeated library ownership lifecycle");
        }
        std::cout << "ABI_TESTS: " << assertions << " assertions, 0 failures\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ABI_TESTS FAILED: " << error.what() << " (after " << assertions << " assertions)\n";
        return 1;
    }
}
