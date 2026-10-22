#include "eab2/c_api.h"
#include "fp_contract.hpp"
#include "build_identity.hpp"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <mutex>
#include <new>
#include <string>
#include <unordered_map>
#include <vector>

#ifdef EAB2_ENABLE_TEST_API
#include "eab2/testing.h"
#include "numeric.hpp"
#endif

namespace {
struct ErrorState {
    uint32_t code = EAB2_OK;
    uint64_t index = UINT64_MAX;
    char field[48]{};
    char message[512]{};
};
struct ContextState {
    uint64_t generation = 1;
    ErrorState error;
};
std::mutex registry_mutex;
std::unordered_map<uint64_t, std::unique_ptr<ContextState>> registry;
uint64_t next_id = 1;

void set_error(ContextState& state, uint32_t code, const char* field,
               uint64_t index, const char* message) noexcept {
    state.error = {};
    state.error.code = code;
    state.error.index = index;
    std::snprintf(state.error.field, sizeof(state.error.field), "%s", field);
    std::snprintf(state.error.message, sizeof(state.error.message), "%s", message);
}
ContextState* lookup(eab2_context token) noexcept {
    if (token.id == 0 || token.owner != token.id ||
        token.type != EAB2_HANDLE_CONTEXT || token.reserved != 0) {
        return nullptr;
    }
    const auto found = registry.find(token.id);
    return found != registry.end() && found->second->generation == token.generation
        ? found->second.get() : nullptr;
}
template<class T> uint32_t header(const T* value) noexcept {
    if (!value || value->struct_size != sizeof(T)) return EAB2_INVALID_INPUT;
    return value->abi_version == EAB2_ABI_VERSION ? EAB2_OK : EAB2_UNSUPPORTED;
}
uint64_t capabilities() noexcept {
    uint64_t result = EAB2_CAP_CONTEXT;
#ifdef EAB2_ENABLE_TEST_API
    result |= EAB2_CAP_TEST_NUMERIC;
#endif
    return result;
}
uint32_t record_exception(eab2_context context, uint32_t code, const char* message) noexcept {
    try {
        std::lock_guard lock(registry_mutex);
        if (auto* state = lookup(context))
            set_error(*state, code, "exception", UINT64_MAX, message);
    } catch (...) { /* A failure to reacquire cannot escape the C boundary. */ }
    return code;
}
}

extern "C" EAB2_API eab2_call_status eab2_get_abi_info(eab2_abi_info* info) {
    try {
        const auto status = header(info);
        if (status != EAB2_OK) return status;
        if (info->reserved) return EAB2_INVALID_INPUT;
        const auto requested = info->requested_capabilities;
        eab2_abi_info result{};
        result.struct_size = sizeof(result);
        result.abi_version = EAB2_ABI_VERSION;
        result.requested_capabilities = requested;
        result.supported_capabilities = capabilities();
        result.unsupported_capabilities = requested & ~capabilities();
        result.context_size = sizeof(eab2_context);
        result.context_options_size = sizeof(eab2_context_options);
        result.error_info_size = sizeof(eab2_error_info);
        result.binary64_bits = 64;
        result.pointer_bits = sizeof(void*) * 8;
        std::snprintf(result.build_identity, sizeof(result.build_identity), "%s", EAB2_BUILD_ID);
        *info = result;
        return result.unsupported_capabilities ? EAB2_UNSUPPORTED : EAB2_OK;
    } catch (...) { return EAB2_INTERNAL_ERROR; }
}

extern "C" EAB2_API eab2_call_status eab2_self_test(void) {
    try { return eab2::fp::self_test(); }
    catch (...) { return EAB2_INTERNAL_ERROR; }
}

extern "C" EAB2_API eab2_call_status eab2_context_create(
    const eab2_context_options* options, eab2_context* output) {
    if (!output) return EAB2_INVALID_INPUT;
    *output = {};
    try {
        const auto status = header(options);
        if (status != EAB2_OK) return status;
        if (options->flags != 0 || options->reserved != 0) return EAB2_INVALID_INPUT;
        const auto fp_status = eab2::fp::self_test();
        if (fp_status != EAB2_OK) return fp_status;
        auto created = std::make_unique<ContextState>();
        std::lock_guard lock(registry_mutex);
        if (next_id == UINT64_MAX) return EAB2_RESOURCE_LIMIT;
        const uint64_t id = next_id++;
        registry.emplace(id, std::move(created));
        *output = {id, id, 1, EAB2_HANDLE_CONTEXT, 0};
        return EAB2_OK;
    } catch (const std::bad_alloc&) { return EAB2_RESOURCE_LIMIT; }
    catch (...) { return EAB2_INTERNAL_ERROR; }
}

extern "C" EAB2_API eab2_call_status eab2_context_destroy(eab2_context context) {
    try {
        std::lock_guard lock(registry_mutex);
        if (!lookup(context)) return EAB2_INVALID_HANDLE;
        registry.erase(context.id);
        return EAB2_OK;
    } catch (...) { return EAB2_INTERNAL_ERROR; }
}

extern "C" EAB2_API eab2_call_status eab2_context_get_error(
    eab2_context context, eab2_error_info* info,
    char* message, uint64_t capacity, uint64_t* required) {
    try {
        std::lock_guard lock(registry_mutex);
        const auto* state = lookup(context);
        if (!state) return EAB2_INVALID_HANDLE;
        const auto status = header(info);
        if (status != EAB2_OK) return status;
        if (!required || (!message && capacity != 0)) return EAB2_INVALID_INPUT;
        const auto needed = std::strlen(state->error.message) + 1;
        *required = needed;
        if (message && capacity < needed) return EAB2_INVALID_INPUT;
        eab2_error_info result{};
        result.struct_size = sizeof(result);
        result.abi_version = EAB2_ABI_VERSION;
        result.code = state->error.code;
        result.index = state->error.index;
        std::memcpy(result.field, state->error.field, sizeof(result.field));
        *info = result;
        if (message) std::memcpy(message, state->error.message, needed);
        return EAB2_OK;
    } catch (...) { return EAB2_INTERNAL_ERROR; }
}

#ifdef EAB2_ENABLE_TEST_API
namespace {
bool extent_fits(uint64_t count, uint64_t stride) noexcept {
    return stride != 0 && count <= std::numeric_limits<size_t>::max() / stride;
}
struct Pending {
    uint32_t status = EAB2_OK;
    std::vector<uint64_t> bits;
    std::string message;
};
}

extern "C" EAB2_API eab2_call_status eab2_numeric_batch(
    eab2_context context, const eab2_numeric_batch_input* input,
    eab2_numeric_batch_output* output) {
    try {
        std::lock_guard lock(registry_mutex);
        auto* state = lookup(context);
        if (!state) return EAB2_INVALID_HANDLE;
        auto reject = [&](uint32_t code, const char* field, uint64_t index,
                          const char* message) {
            set_error(*state, code, field, index, message);
            return code;
        };
        const auto fp_status = eab2::fp::self_test();
        if (fp_status != EAB2_OK)
            return reject(fp_status, "environment", UINT64_MAX, "floating-point contract failed");
        const auto in_status = header(input), out_status = header(output);
        if (in_status != EAB2_OK) return reject(in_status, "input", UINT64_MAX, "invalid batch input header");
        if (out_status != EAB2_OK) return reject(out_status, "output", UINT64_MAX, "invalid batch output header");
        if (input->item_stride != sizeof(eab2_numeric_input) ||
            output->item_stride != sizeof(eab2_numeric_output) ||
            !extent_fits(input->item_count, input->item_stride) ||
            !extent_fits(output->item_capacity, output->item_stride) ||
            output->item_capacity < input->item_count ||
            (input->item_count && (!input->items || !output->items)))
            return reject(EAB2_INVALID_INPUT, "items", UINT64_MAX, "invalid count, stride, capacity, or pointer");
        constexpr uint64_t max_items = 65536, max_values = 65536, max_text = 1048576;
        if (input->item_count > max_items)
            return reject(EAB2_RESOURCE_LIMIT, "item_count", UINT64_MAX, "test protocol item limit exceeded");
        // Validate every descriptor before performing any computation or writes.
        for (uint64_t i = 0; i < input->item_count; ++i) {
            const auto& in = input->items[i];
            const auto& out = output->items[i];
            const auto item_input_status = header(&in), item_output_status = header(&out);
            if (item_input_status != EAB2_OK)
                return reject(item_input_status, "item_input", i, "invalid item input header");
            if (item_output_status != EAB2_OK)
                return reject(item_output_status, "item_output", i, "invalid item output header");
            if (in.reserved || out.reserved || (in.flags & ~EAB2_NUMERIC_ALLOW_UNDERFLOW) ||
                in.value_stride != sizeof(eab2_text) ||
                !extent_fits(in.value_count, in.value_stride) ||
                !extent_fits(out.bits_capacity, sizeof(uint64_t)) ||
                (in.value_count && !in.values) || (out.bits_capacity && !out.bits))
                return reject(EAB2_INVALID_INPUT, "item_descriptor", i, "invalid item header, flags, stride, or buffer");
            if (in.value_count > max_values)
                return reject(EAB2_RESOURCE_LIMIT, "value_count", i, "test protocol value limit exceeded");
            for (uint64_t j = 0; j < in.value_count; ++j) {
                if (!in.values[j].data || !in.values[j].length)
                    return reject(EAB2_INVALID_INPUT, "values", i, "empty or null input text");
                if (in.values[j].length > max_text)
                    return reject(EAB2_RESOURCE_LIMIT, "values", i, "test protocol text limit exceeded");
            }
        }
        // Stage all results. Catastrophic allocation failure leaves outputs untouched.
        std::vector<Pending> pending(static_cast<size_t>(input->item_count));
        for (uint64_t i = 0; i < input->item_count; ++i) {
            const auto& in = input->items[i];
            auto& result = pending[static_cast<size_t>(i)];
            try {
                std::vector<std::string> values;
                values.reserve(static_cast<size_t>(in.value_count));
                for (uint64_t j = 0; j < in.value_count; ++j)
                    values.emplace_back(in.values[j].data, static_cast<size_t>(in.values[j].length));
                result.bits = eab2::numeric::evaluate(in.operation, in.encoding, values,
                    (in.flags & EAB2_NUMERIC_ALLOW_UNDERFLOW) != 0);
                if (result.bits.size() > output->items[i].bits_capacity) {
                    result.status = EAB2_INVALID_INPUT;
                    result.message = "insufficient result bits capacity";
                    result.bits.clear();
                }
            } catch (const eab2::numeric::Error& error) {
                result.status = error.code >= EAB2_INVALID_INPUT && error.code <= EAB2_CANCELLED
                    ? error.code : EAB2_INTERNAL_ERROR;
                result.message = error.what();
            } catch (const std::bad_alloc&) { throw; }
            catch (const std::exception& error) {
                result.status = EAB2_INTERNAL_ERROR;
                result.message = error.what();
            } catch (...) {
                result.status = EAB2_INTERNAL_ERROR;
                result.message = "unexpected numeric exception";
            }
        }
        state->error = {};
        bool recorded_error = false;
        for (uint64_t i = 0; i < input->item_count; ++i) {
            auto& out = output->items[i];
            const auto& result = pending[static_cast<size_t>(i)];
            out.call_status = result.status;
            out.mathematical_status = result.status == EAB2_OK ? EAB2_MATH_VALUE : EAB2_MATH_NOT_COMPUTED;
            out.display_status = result.status == EAB2_OK ? EAB2_DISPLAY_VALID :
                result.status == EAB2_CONSTRUCTION_RANGE ? EAB2_DISPLAY_RANGE : EAB2_DISPLAY_NOT_AVAILABLE;
            out.bits_count = result.status == EAB2_OK ? result.bits.size() : 0;
            if (result.status == EAB2_OK) {
                if (!result.bits.empty()) std::copy(result.bits.begin(), result.bits.end(), out.bits);
            } else if (!recorded_error) {
                set_error(*state, result.status, "numeric", i, result.message.c_str());
                recorded_error = true;
            }
        }
        output->item_count = input->item_count;
        return EAB2_OK;
    } catch (const std::bad_alloc&) {
        return record_exception(context, EAB2_RESOURCE_LIMIT, "batch allocation failed; outputs unchanged");
    } catch (...) {
        return record_exception(context, EAB2_INTERNAL_ERROR, "unexpected batch boundary exception; outputs unchanged");
    }
}
#endif
