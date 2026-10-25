#if defined(__AVX__)
#error eab2 controlled sources require the x64 SSE2 compilation target
#endif
#include "eab2/c_api.h"
#include "fp_contract.hpp"
#include "build_identity.hpp"
#include "geometry2.hpp"
#include "numeric.hpp"
#include "l1.hpp"
#include "opt.hpp"
#include "statics.hpp"
#include "critical.hpp"
#include "sensitivity.hpp"
#include "geometry_seed.hpp"

#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <map>
#include <mutex>
#include <new>
#include <string>
#include <set>
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
struct Object {
    uint64_t generation = 0;
    uint32_t type = 0;
    uint32_t flags = 0;
    std::unique_ptr<eab2::geometry2::Body> body;
    std::unique_ptr<eab2::geometry2::Entrance> entrance;
    std::unique_ptr<std::string> json;
    std::unique_ptr<eab2::contact::Assembly2> assembly;
    std::unique_ptr<eab2::contact::ContactSet2> contacts;
    std::unique_ptr<eab2::statics::LimitResult2> limit_result;
    std::unique_ptr<eab2::statics::CriticalParameter2> critical_result;
    std::shared_ptr<const eab2::contact::ContactSet2> sensitivity_contacts;
};
struct ContextState {
    std::mutex mutex;
    bool alive = true;
    uint64_t generation = 0;
    ErrorState error;
    eab2::geometry2::GeometryLimits limits;
    std::vector<Object> objects;
};
std::mutex registry_mutex;
std::unordered_map<uint64_t, std::shared_ptr<ContextState>> registry;
uint64_t next_id = 1;
std::atomic<uint64_t> next_generation{1};
uint64_t generation() {
    auto value = next_generation.load(std::memory_order_relaxed);
    do {
        if (value == UINT64_MAX) throw eab2::numeric::Error(EAB2_RESOURCE_LIMIT, "handle generation exhausted");
    } while (!next_generation.compare_exchange_weak(value, value + 1, std::memory_order_relaxed));
    return value;
}

void set_error(ContextState& state, uint32_t code, const char* field,
               uint64_t index, const char* message) noexcept {
    state.error = {};
    state.error.code = code;
    state.error.index = index;
    std::snprintf(state.error.field, sizeof(state.error.field), "%s", field);
    std::snprintf(state.error.message, sizeof(state.error.message), "%s", message);
}
// Registry lock only pins ownership. It is NEVER held while waiting for a
// context mutex, so distinct contexts compute concurrently and destroy is safe.
std::shared_ptr<ContextState> resolve(eab2_context token) {
    if (token.id == 0 || token.owner != token.id ||
        token.type != EAB2_HANDLE_CONTEXT || token.reserved != 0) return {};
    std::lock_guard lock(registry_mutex);
    const auto found = registry.find(token.id);
    return found != registry.end() && found->second && found->second->generation == token.generation
        ? found->second : std::shared_ptr<ContextState>{};
}
struct ContextAccess {
    std::shared_ptr<ContextState> owner;
    std::unique_lock<std::mutex> lock;
    explicit ContextAccess(eab2_context token) : owner(resolve(token)) {
        if (owner) lock = std::unique_lock(owner->mutex);
    }
    ContextState* get() const { return owner && owner->alive ? owner.get() : nullptr; }
};
template<class T> uint32_t header(const T* value) noexcept {
    if (!value || value->struct_size != sizeof(T)) return EAB2_INVALID_INPUT;
    return value->abi_version == EAB2_ABI_VERSION ? EAB2_OK : EAB2_UNSUPPORTED;
}
uint64_t capabilities() noexcept {
    uint64_t result = EAB2_CAP_CONTEXT | EAB2_CAP_BODY2 | EAB2_CAP_ENTRANCE2 |
        EAB2_CAP_QUERY2 | EAB2_CAP_EXPORT_EXACT | EAB2_CAP_LOCAL2 | EAB2_CAP_LIMITS2 |
        EAB2_CAP_ASSEMBLY2 | EAB2_CAP_CONTACTSET2 | EAB2_CAP_LOCK2 | EAB2_CAP_MOBILITY2 |
        EAB2_CAP_LIMIT2 | EAB2_CAP_CRITICAL_PARAMETER | EAB2_CAP_SENSITIVITY2;
#ifdef EAB2_ENABLE_TEST_API
    result |= EAB2_CAP_TEST_NUMERIC | EAB2_CAP_TEST_EXACT2 | EAB2_CAP_TEST_OPT;
#endif
    return result;
}
uint32_t record_exception(eab2_context context, uint32_t code, const char* message) noexcept {
    try {
        ContextAccess access(context);
        if (auto* state = access.get())
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
        auto created = std::make_shared<ContextState>();
        std::lock_guard lock(registry_mutex);
        uint64_t id = 0;
        for (const auto& entry : registry) if (!entry.second) { id = entry.first; break; }
        if (!id) {
            if (next_id == UINT64_MAX) return EAB2_RESOURCE_LIMIT;
            id = next_id++;
        }
        created->generation = generation();
        const auto gen = created->generation;
        registry[id] = std::move(created);
        *output = {id, id, gen, EAB2_HANDLE_CONTEXT, 0};
        return EAB2_OK;
    } catch (const eab2::numeric::Error& error) { return error.code; }
    catch (const std::bad_alloc&) { return EAB2_RESOURCE_LIMIT; }
    catch (...) { return EAB2_INTERNAL_ERROR; }
}

extern "C" EAB2_API eab2_call_status eab2_context_destroy(eab2_context context) {
    try {
        ContextAccess access(context);
        if (!access.get()) return EAB2_INVALID_HANDLE;
        access.owner->alive = false;
        access.owner->objects.clear();
        std::lock_guard lock(registry_mutex);
        registry[context.id].reset();
        return EAB2_OK;
    } catch (...) { return EAB2_INTERNAL_ERROR; }
}

extern "C" EAB2_API eab2_call_status eab2_context_get_error(
    eab2_context context, eab2_error_info* info,
    char* message, uint64_t capacity, uint64_t* required) {
    try {
        ContextAccess access(context);
        const auto* state = access.get();
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

namespace {
Object* object(ContextState& state, eab2_context owner, eab2_context token, uint32_t type) {
    if (!token.id || token.owner != owner.id || token.type != type || token.reserved ||
        token.id > state.objects.size()) return nullptr;
    auto& slot = state.objects[static_cast<size_t>(token.id - 1)];
    return slot.type == type && slot.generation == token.generation ? &slot : nullptr;
}
eab2_context add_object(ContextState& state, eab2_context owner, Object value) {
    value.generation = generation();
    size_t at = 0;
    for (; at < state.objects.size(); ++at) if (!state.objects[at].type) break;
    const auto gen = value.generation;
    const auto type = value.type;
    if (at == state.objects.size()) state.objects.push_back(std::move(value));
    else state.objects[at] = std::move(value);
    return {owner.id, at + 1, gen, type, 0};
}
uint32_t reject_c1(ContextState& state, uint32_t code, const char* field, const char* message,
                   uint64_t index = UINT64_MAX) {
    set_error(state, code, field, index, message);
    return code;
}
struct IndexedInputError : std::runtime_error {
    uint32_t code; std::string field; uint64_t index;
    IndexedInputError(uint32_t c, std::string f, uint64_t i, const std::string& message)
        : std::runtime_error(message), code(c), field(std::move(f)), index(i) {}
};
template<class Function> uint32_t c1_call(eab2_context context, Function function, bool requires_fp = true) noexcept {
    try {
        ContextAccess access(context);
        auto* state = access.get();
        if (!state) return EAB2_INVALID_HANDLE;
        state->error = {};
        const auto fp_status = requires_fp ? eab2::fp::self_test() : EAB2_OK;
        if (fp_status != EAB2_OK)
            return reject_c1(*state, fp_status, "environment", "floating-point contract failed");
        eab2::exact::IntegerLimitScope integer_scope(state->limits.max_integer_bits);
        eab2::geometry2::GeometryWorkScope work_scope(state->limits);
        return function(*state);
    } catch (const IndexedInputError& error) {
        ContextAccess access(context);
        const auto state = access.get();
        return state ? reject_c1(*state, error.code, error.field.c_str(), error.what(), error.index) : EAB2_INVALID_HANDLE;
    } catch (const eab2::exact::ResourceLimit& error) {
        return record_exception(context, EAB2_RESOURCE_LIMIT, error.what());
    } catch (const eab2::numeric::Error& error) {
        return record_exception(context, error.code, error.what());
    } catch (const std::invalid_argument& error) {
        return record_exception(context, EAB2_INVALID_INPUT, error.what());
    } catch (const std::bad_alloc&) {
        return record_exception(context, EAB2_RESOURCE_LIMIT, "allocation failed; output not committed");
    } catch (const std::exception& error) {
        return record_exception(context, EAB2_INTERNAL_ERROR, error.what());
    } catch (...) {
        return record_exception(context, EAB2_INTERNAL_ERROR, "unexpected geometry boundary exception");
    }
}
bool c1_extent(uint64_t count, uint64_t stride) {
    return stride != 0 && count <= std::numeric_limits<size_t>::max() / stride;
}
uint32_t destroy_object(eab2_context context, eab2_context token, uint32_t type) {
    return c1_call(context, [&](ContextState& state) {
        auto* found = object(state, context, token, type);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "handle", "wrong owner, type, or generation");
        *found = {};
        return EAB2_OK;
    }, false);
}
template<class Input, class Decode>
uint32_t query2_impl(eab2_context context, eab2_entrance2 entrance, const Input* input,
                     eab2_query2_output* output, uint64_t stride, Decode decode) {
    return c1_call(context, [&](ContextState& state) {
        auto* found = object(state, context, entrance, EAB2_HANDLE_ENTRANCE2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "entrance", "invalid entrance handle");
        auto status = header(input);
        if (status != EAB2_OK) return reject_c1(state, status, "input", "invalid query input header");
        status = header(output);
        if (status != EAB2_OK) return reject_c1(state, status, "output", "invalid query output header");
        if (input->point_stride != stride || output->item_stride != sizeof(eab2_query2_item) ||
            !c1_extent(input->point_count, stride) || !c1_extent(output->item_capacity, output->item_stride) ||
            output->item_capacity < input->point_count ||
            (input->point_count && (!input->points || !output->items)))
            return reject_c1(state, EAB2_INVALID_INPUT, "points", "invalid count, stride, pointer, or capacity");
        if (input->point_count > 65536)
            return reject_c1(state, EAB2_RESOURCE_LIMIT, "points", "query point limit exceeded");
        std::vector<eab2_query2_item> pending;
        pending.reserve(static_cast<size_t>(input->point_count));
        for (uint64_t i = 0; i < input->point_count; ++i) {
            eab2_query2_item item{EAB2_OK, EAB2_MATH_VALUE, UINT32_MAX, UINT32_MAX};
            try {
                const auto point = decode(input->points[i]);
                item.body_state = static_cast<uint32_t>(found->entrance->membership(point) + 1);
                item.topology_state = static_cast<uint32_t>(found->entrance->topology(point) + 1);
            } catch (const eab2::exact::ResourceLimit& error) {
                item = {EAB2_RESOURCE_LIMIT, EAB2_MATH_NOT_COMPUTED, UINT32_MAX, UINT32_MAX};
                if (state.error.code == EAB2_OK) reject_c1(state, EAB2_RESOURCE_LIMIT, "points", error.what(), i);
            } catch (const eab2::numeric::Error& error) {
                item = {error.code, EAB2_MATH_NOT_COMPUTED, UINT32_MAX, UINT32_MAX};
                if (state.error.code == EAB2_OK) reject_c1(state, error.code, "points", error.what(), i);
            } catch (const std::invalid_argument& error) {
                item = {EAB2_INVALID_INPUT, EAB2_MATH_NOT_COMPUTED, UINT32_MAX, UINT32_MAX};
                if (state.error.code == EAB2_OK) reject_c1(state, EAB2_INVALID_INPUT, "points", error.what(), i);
            }
            pending.push_back(item);
        }
        if (!pending.empty()) std::copy(pending.begin(), pending.end(), output->items);
        output->item_count = pending.size();
        return EAB2_OK;
    });
}
uint32_t export2_impl(eab2_context context, eab2_entrance2 entrance, eab2_exact_result* output, bool local) {
    return c1_call(context, [&](ContextState& state) {
        auto* found = object(state, context, entrance, EAB2_HANDLE_ENTRANCE2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "entrance", "invalid entrance handle");
        const auto status = header(output);
        if (status != EAB2_OK) return reject_c1(state, status, "output", "invalid exact-result header");
        Object created;
        created.type = EAB2_HANDLE_RESULT;
        // Cache-off is a real lifetime boundary, not an alias for merge/compact.
        std::unique_ptr<eab2::geometry2::Entrance> transient;
        const auto* source = found->entrance.get();
        if (found->flags & EAB2_ENTRANCE_NO_CACHE) {
            transient = std::make_unique<eab2::geometry2::Entrance>(source->a, source->b,
                !(found->flags & EAB2_ENTRANCE_NO_MERGE), !(found->flags & EAB2_ENTRANCE_NO_COMPACT), source->limits());
            source = transient.get();
        }
        created.json = std::make_unique<std::string>(local ? source->local_origin_exact() : source->export_exact());
        const auto* data = created.json->c_str();
        const auto count = created.json->size();
        const auto token = add_object(state, context, std::move(created));
        *output = {sizeof(eab2_exact_result), EAB2_ABI_VERSION, EAB2_OK, EAB2_MATH_VALUE, token, data, count};
        return EAB2_OK;
    });
}
}

extern "C" EAB2_API eab2_call_status eab2_context_get_limits2(eab2_context context, eab2_context_limits2* output) {
    return c1_call(context, [&](ContextState& state) {
        const auto status = header(output);
        if (status != EAB2_OK) return reject_c1(state, status, "limits", "invalid limits output header");
        *output = {sizeof(eab2_context_limits2), EAB2_ABI_VERSION, state.limits.max_work_units,
            state.limits.max_elements, state.limits.max_integer_bits};
        return EAB2_OK;
    }, false);
}
extern "C" EAB2_API eab2_call_status eab2_context_configure_limits2(eab2_context context, const eab2_context_limits2* input) {
    return c1_call(context, [&](ContextState& state) {
        const auto status = header(input);
        if (status != EAB2_OK) return reject_c1(state, status, "limits", "invalid limits input header");
        if (!input->max_work_units || !input->max_elements || !input->max_integer_bits ||
            input->max_elements > std::numeric_limits<size_t>::max() || input->max_integer_bits > std::numeric_limits<size_t>::max())
            return reject_c1(state, EAB2_INVALID_INPUT, "limits", "all limits must be positive explicit supported integers");
        for (const auto& slot : state.objects) if (slot.type)
            return reject_c1(state, EAB2_INVALID_INPUT, "limits", "cannot reconfigure while child objects exist");
        state.limits = {input->max_work_units, static_cast<size_t>(input->max_elements), static_cast<size_t>(input->max_integer_bits)};
        return EAB2_OK;
    });
}
extern "C" EAB2_API eab2_call_status eab2_get_c1_abi_info(eab2_c1_abi_info* info) {
    const auto status = header(info);
    if (status != EAB2_OK) return status;
    if (info->reserved) return EAB2_INVALID_INPUT;
    *info = {sizeof(eab2_c1_abi_info), EAB2_ABI_VERSION, sizeof(eab2_body2_input),
        sizeof(eab2_entrance2_options), sizeof(eab2_query2_input), sizeof(eab2_query2_item),
        sizeof(eab2_query2_output), sizeof(eab2_exact_result), sizeof(eab2_point2_bits), 0};
    return EAB2_OK;
}
extern "C" EAB2_API eab2_call_status eab2_body2_create(eab2_context context,
    const eab2_body2_input* input, eab2_body2* output) {
    if (!output) return EAB2_INVALID_INPUT;
    *output = {};
    return c1_call(context, [&](ContextState& state) {
        const auto status = header(input);
        if (status != EAB2_OK) return reject_c1(state, status, "input", "invalid body input header");
        if (input->flags || input->reserved || input->vertex_stride != sizeof(eab2_point2_bits) ||
            !c1_extent(input->vertex_count, input->vertex_stride) || input->vertex_count < 3 || !input->vertices)
            return reject_c1(state, EAB2_INVALID_INPUT, "vertices", "invalid body descriptor");
        if (input->vertex_count > 4096)
            return reject_c1(state, EAB2_RESOURCE_LIMIT, "vertices", "body vertex limit exceeded");
        std::vector<std::array<uint64_t, 2>> bits;
        bits.reserve(static_cast<size_t>(input->vertex_count));
        for (uint64_t i = 0; i < input->vertex_count; ++i)
            bits.push_back({input->vertices[i].x_bits, input->vertices[i].y_bits});
        Object created;
        created.type = EAB2_HANDLE_BODY2;
        created.body = std::make_unique<eab2::geometry2::Body>(eab2::geometry2::Body::from_bits(bits, state.limits));
        *output = add_object(state, context, std::move(created));
        return EAB2_OK;
    });
}
extern "C" EAB2_API eab2_call_status eab2_body2_destroy(eab2_context context, eab2_body2 body) {
    return destroy_object(context, body, EAB2_HANDLE_BODY2);
}
extern "C" EAB2_API eab2_call_status eab2_entrance2_create(eab2_context context,
    eab2_body2 a, eab2_body2 b, const eab2_entrance2_options* options, eab2_entrance2* output) {
    if (!output) return EAB2_INVALID_INPUT;
    *output = {};
    return c1_call(context, [&](ContextState& state) {
        const auto status = header(options);
        if (status != EAB2_OK) return reject_c1(state, status, "options", "invalid entrance options header");
        if (options->reserved || (options->flags & ~(EAB2_ENTRANCE_NO_MERGE | EAB2_ENTRANCE_NO_COMPACT | EAB2_ENTRANCE_NO_CACHE)))
            return reject_c1(state, EAB2_INVALID_INPUT, "options", "unknown entrance flags");
        auto* first = object(state, context, a, EAB2_HANDLE_BODY2);
        auto* second = object(state, context, b, EAB2_HANDLE_BODY2);
        if (!first || !second) return reject_c1(state, EAB2_INVALID_HANDLE, "bodies", "invalid body handle");
        Object created;
        created.type = EAB2_HANDLE_ENTRANCE2;
        created.flags = options->flags;
        created.entrance = std::make_unique<eab2::geometry2::Entrance>(*first->body, *second->body,
            !(options->flags & EAB2_ENTRANCE_NO_MERGE), !(options->flags & EAB2_ENTRANCE_NO_COMPACT), state.limits);
        *output = add_object(state, context, std::move(created));
        return EAB2_OK;
    });
}
extern "C" EAB2_API eab2_call_status eab2_entrance2_destroy(eab2_context context, eab2_entrance2 entrance) {
    return destroy_object(context, entrance, EAB2_HANDLE_ENTRANCE2);
}
extern "C" EAB2_API eab2_call_status eab2_query2_batch(eab2_context context, eab2_entrance2 entrance,
    const eab2_query2_input* input, eab2_query2_output* output) {
    return query2_impl(context, entrance, input, output, sizeof(eab2_point2_bits), [](const eab2_point2_bits& point) {
        return eab2::geometry2::Point{eab2::numeric::decode_binary64(point.x_bits), eab2::numeric::decode_binary64(point.y_bits)};
    });
}
extern "C" EAB2_API eab2_call_status eab2_membership2_batch(eab2_context context, eab2_entrance2 entrance,
    const eab2_query2_input* input, eab2_query2_output* output) { return eab2_query2_batch(context, entrance, input, output); }
extern "C" EAB2_API eab2_call_status eab2_topology2_batch(eab2_context context, eab2_entrance2 entrance,
    const eab2_query2_input* input, eab2_query2_output* output) { return eab2_query2_batch(context, entrance, input, output); }
extern "C" EAB2_API eab2_call_status eab2_result_export_exact(eab2_context context,
    eab2_entrance2 entrance, eab2_exact_result* output) { return export2_impl(context, entrance, output, false); }
extern "C" EAB2_API eab2_call_status eab2_local_origin2_exact(eab2_context context,
    eab2_entrance2 entrance, eab2_exact_result* output) { return export2_impl(context, entrance, output, true); }
extern "C" EAB2_API eab2_call_status eab2_result_destroy(eab2_context context, eab2_result result) {
    return destroy_object(context, result, EAB2_HANDLE_RESULT);
}
#ifdef EAB2_ENABLE_TEST_API
extern "C" EAB2_API eab2_call_status eab2_query2_exact_batch(eab2_context context, eab2_entrance2 entrance,
    const eab2_query2_exact_input* input, eab2_query2_output* output) {
    uint64_t parse_work = 0;
    return query2_impl(context, entrance, input, output, sizeof(eab2_point2_exact), [&](const eab2_point2_exact& point) {
        auto parse = [&](const eab2_text& text) {
            if (!text.data || !text.length) throw eab2::numeric::Error(EAB2_INVALID_INPUT, "empty exact coordinate");
            if (text.length > 4096) throw eab2::numeric::Error(EAB2_RESOURCE_LIMIT, "exact coordinate parse work limit");
            const uint64_t work = text.length * text.length;
            if (work > UINT64_C(67108864) - parse_work)
                throw eab2::numeric::Error(EAB2_RESOURCE_LIMIT, "exact query aggregate parsing work limit");
            parse_work += work;
            return eab2::numeric::parse_rational(std::string(text.data, static_cast<size_t>(text.length)));
        };
        return eab2::geometry2::Point{parse(point.x), parse(point.y)};
    });
}
extern "C" EAB2_API eab2_call_status eab2_covers2_exact(eab2_context context,
    eab2_entrance2 entrance, const eab2_covers2_input* input, eab2_exact_result* output) {
    return c1_call(context, [&](ContextState& state) {
        auto* found = object(state, context, entrance, EAB2_HANDLE_ENTRANCE2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "entrance", "invalid entrance handle");
        auto status = header(input);
        if (status != EAB2_OK) return reject_c1(state, status, "input", "invalid covers descriptor");
        status = header(output);
        if (status != EAB2_OK) return reject_c1(state, status, "output", "invalid exact result descriptor");
        if (input->reserved || input->require_in_segment > 1)
            return reject_c1(state, EAB2_INVALID_INPUT, "flags", "invalid covers options");
        auto parse = [](const eab2_text& text, bool required) -> std::optional<eab2::exact::Rational> {
            if (!text.data && !text.length && !required) return std::nullopt;
            if (!text.data || !text.length) throw eab2::numeric::Error(EAB2_INVALID_INPUT, "invalid covers parameter");
            if (text.length > 4096) throw eab2::numeric::Error(EAB2_RESOURCE_LIMIT, "covers decimal parse work limit");
            const auto value = eab2::numeric::parse_rational(std::string(text.data, static_cast<size_t>(text.length)));
            if (value.sign() < 0) throw eab2::numeric::Error(EAB2_INVALID_INPUT, "negative covers tolerance/window");
            return value;
        };
        const auto window = parse(input->window, false), tol = parse(input->tol, true);
        const auto cone = parse(input->cone_tol, false), segment = parse(input->seg_tol, false);
        Object created;
        created.type = EAB2_HANDLE_RESULT;
        created.json = std::make_unique<std::string>(eab2::geometry2::covers_exact_json(
            found->entrance->a.vertices, found->entrance->b.vertices, window,
            input->require_in_segment != 0, *tol, cone, segment));
        const auto* data = created.json->c_str();
        const auto count = created.json->size();
        const auto token = add_object(state, context, std::move(created));
        *output = {sizeof(eab2_exact_result), EAB2_ABI_VERSION, EAB2_OK, EAB2_MATH_VALUE, token, data, count};
        return EAB2_OK;
    });
}

#endif

#ifdef EAB2_ENABLE_TEST_API
namespace {
bool extent_fits(uint64_t count, uint64_t stride) noexcept {
    return stride != 0 && count <= std::numeric_limits<size_t>::max() / stride;
}
struct Pending {
    uint32_t status = EAB2_OK;
    std::vector<uint64_t> bits;
    std::string message;
    bool underflow_zero = false;
};
}

extern "C" EAB2_API eab2_call_status eab2_numeric_batch(
    eab2_context context, const eab2_numeric_batch_input* input,
    eab2_numeric_batch_output* output) {
    try {
        ContextAccess access(context);
        auto* state = access.get();
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
        uint64_t total_values = 0, total_text = 0, parse_work = 0;
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
            total_values += in.value_count;
            if (total_values > max_values)
                return reject(EAB2_RESOURCE_LIMIT, "values", i, "aggregate value work limit exceeded");
            for (uint64_t j = 0; j < in.value_count; ++j) {
                if (!in.values[j].data || !in.values[j].length)
                    return reject(EAB2_INVALID_INPUT, "values", i, "empty or null input text");
                if (in.values[j].length > max_text)
                    return reject(EAB2_RESOURCE_LIMIT, "values", i, "test protocol text limit exceeded");
                const auto length = in.values[j].length;
                total_text += length;
                parse_work += length * length;
                if (total_text > 4194304 || parse_work > 67108864)
                    return reject(EAB2_RESOURCE_LIMIT, "values", i, "aggregate parsing work limit exceeded");
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
                eab2::exact::IntegerLimitScope integer_scope(state->limits.max_integer_bits);
                result.bits = eab2::numeric::evaluate(in.operation, in.encoding, values,
                    (in.flags & EAB2_NUMERIC_ALLOW_UNDERFLOW) != 0, &result.underflow_zero);
                if (result.bits.size() > output->items[i].bits_capacity) {
                    result.status = EAB2_INVALID_INPUT;
                    result.message = "insufficient result bits capacity";
                    result.bits.clear();
                }
            } catch (const eab2::exact::ResourceLimit& error) {
                result.status = EAB2_RESOURCE_LIMIT;
                result.message = error.what();
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
            out.display_status = result.status == EAB2_OK ?
                (result.underflow_zero ? EAB2_DISPLAY_UNDERFLOW_ZERO : EAB2_DISPLAY_VALID) :
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

namespace {
uint32_t l1_math(const std::optional<std::string>& name) {
    if (!name) return EAB2_MATH_NOT_COMPUTED;
    if (*name == "OVERLAP") return EAB2_MATH_OVERLAP;
    if (*name == "UNPROVED") return EAB2_MATH_UNPROVED;
    if (*name == "MECHANICAL_UNRESOLVED") return EAB2_MATH_MECHANICAL_UNRESOLVED;
    return EAB2_MATH_VALUE;
}
uint32_t save_exact(ContextState& state, eab2_context context, std::string json,
                    uint32_t math, eab2_exact_result* output,
                    std::unique_ptr<eab2::statics::LimitResult2> limit = {},
                    std::unique_ptr<eab2::statics::CriticalParameter2> critical = {},
                    std::shared_ptr<const eab2::contact::ContactSet2> contacts = {}) {
    Object created;
    created.type = EAB2_HANDLE_RESULT;
    created.json = std::make_unique<std::string>(std::move(json));
    created.limit_result = std::move(limit);
    created.critical_result = std::move(critical);
    created.sensitivity_contacts = std::move(contacts);
    const auto* data = created.json->c_str();
    const auto count = created.json->size();
    const auto token = add_object(state, context, std::move(created));
    *output = {sizeof(eab2_exact_result), EAB2_ABI_VERSION, EAB2_OK, math, token, data, count};
    return EAB2_OK;
}
bool valid_utf8(const std::string& text) {
    size_t at = 0;
    while (at < text.size()) {
        const auto first = static_cast<unsigned char>(text[at++]);
        if (first < 128) continue;
        unsigned width = 0, value = 0, minimum = 0;
        if (first >= 0xc2 && first <= 0xdf) { width = 1; value = first & 31; minimum = 0x80; }
        else if (first >= 0xe0 && first <= 0xef) { width = 2; value = first & 15; minimum = 0x800; }
        else if (first >= 0xf0 && first <= 0xf4) { width = 3; value = first & 7; minimum = 0x10000; }
        else return false;
        if (width > text.size() - at) return false;
        for (unsigned k = 0; k < width; ++k) {
            const auto next = static_cast<unsigned char>(text[at++]);
            if ((next & 0xc0) != 0x80) return false;
            value = (value << 6) | (next & 63);
        }
        if (value < minimum || value > 0x10ffff || (value >= 0xd800 && value <= 0xdfff)) return false;
    }
    return true;
}
eab2::geometry2::Point decode_point(eab2_point2_bits point) {
    return {eab2::numeric::decode_binary64(point.x_bits), eab2::numeric::decode_binary64(point.y_bits)};
}
}
extern "C" EAB2_API eab2_call_status eab2_get_c3l1_abi_info(eab2_c3l1_abi_info* info) {
    const auto status = header(info);
    if (status != EAB2_OK) return status;
    if (info->reserved) return EAB2_INVALID_INPUT;
    *info = {sizeof(eab2_c3l1_abi_info), EAB2_ABI_VERSION, sizeof(eab2_assembly_body2),
        sizeof(eab2_assembly2_input), sizeof(eab2_pair2), sizeof(eab2_lock2_input), sizeof(eab2_string), 0};
    return EAB2_OK;
}
extern "C" EAB2_API eab2_call_status eab2_assembly2_create(eab2_context context,
    const eab2_assembly2_input* input, eab2_assembly2* output) {
    if (!output) return EAB2_INVALID_INPUT;
    *output = {};
    return c1_call(context, [&](ContextState& state) {
        const auto status = header(input);
        if (status != EAB2_OK) return reject_c1(state, status, "input", "invalid assembly input header");
        if (input->profile != EAB2_PROFILE1)
            return reject_c1(state, EAB2_UNSUPPORTED, "profile", "only profile1 is implemented");
        if ((input->flags & ~(EAB2_ASSEMBLY_COMPLETE | EAB2_ASSEMBLY_EXPLICIT_PAIRS)) ||
            !input->body_count || input->body_stride != sizeof(eab2_assembly_body2) || !input->bodies ||
            input->pair_stride != sizeof(eab2_pair2) || (input->pair_count && !input->pairs) ||
            !c1_extent(input->body_count, input->body_stride) || !c1_extent(input->pair_count, input->pair_stride) ||
            (!(input->flags & EAB2_ASSEMBLY_EXPLICIT_PAIRS) && (input->pair_count || (input->flags & EAB2_ASSEMBLY_COMPLETE))))
            return reject_c1(state, EAB2_INVALID_INPUT, "assembly", "invalid body/pair counts, pointers, strides or flags");
        if (input->body_count > 1024 || input->pair_count > state.limits.max_elements)
            return reject_c1(state, EAB2_RESOURCE_LIMIT, "assembly", "assembly descriptor work limit exceeded");
        auto value = std::make_unique<eab2::contact::Assembly2>();
        value->limits = state.limits;
        value->completeness = input->flags & EAB2_ASSEMBLY_COMPLETE ? "complete" : "completeness_unknown";
        std::set<std::string> ids;
        for (uint64_t i = 0; i < input->body_count; ++i) {
            const auto& entry = input->bodies[i];
            const auto entry_status = header(&entry);
            if (entry_status != EAB2_OK) return reject_c1(state, entry_status, "body", "invalid body entry header", i);
            const auto* body = object(state, context, entry.body, EAB2_HANDLE_BODY2);
            if (!body) return reject_c1(state, EAB2_INVALID_HANDLE, "body", "invalid assembly body handle", i);
            if (!entry.body_id.length || !entry.body_id.data || entry.dof_mask > 7 || entry.boundary_type > 2)
                return reject_c1(state, EAB2_INVALID_INPUT, "body", "invalid id/mask/boundary", i);
            if (entry.body_id.length > 4096)
                return reject_c1(state, EAB2_RESOURCE_LIMIT, "body_id", "identifier length limit exceeded", i);
            std::string id(entry.body_id.data, static_cast<size_t>(entry.body_id.length));
            if (!valid_utf8(id) || !ids.insert(id).second)
                return reject_c1(state, EAB2_INVALID_INPUT, "body_id", "duplicate or invalid UTF-8 identifier", i);
            const std::string boundary = entry.boundary_type == EAB2_FIXED_BODY ? "FIXED_BODY" :
                entry.boundary_type == EAB2_FORCE_CONTROLLED_PLATE ? "FORCE_CONTROLLED_PLATE" : "";
            std::array<int, 3> mask{int(entry.dof_mask & 1), int((entry.dof_mask >> 1) & 1), int((entry.dof_mask >> 2) & 1)};
            value->bodies.emplace_back(std::move(id), *body->body, decode_point(entry.reference_point),
                boundary, mask, decode_point(entry.dof_anchor));
        }
        if (input->flags & EAB2_ASSEMBLY_EXPLICIT_PAIRS) {
            value->pairs.emplace();
            std::set<std::array<size_t, 2>> pairs;
            for (uint64_t i = 0; i < input->pair_count; ++i) {
                const auto pair = input->pairs[i];
                if (pair.a >= input->body_count || pair.b >= input->body_count || pair.a == pair.b)
                    return reject_c1(state, EAB2_INVALID_INPUT, "pairs", "invalid candidate pair", i);
                value->pairs->push_back({static_cast<size_t>(pair.a), static_cast<size_t>(pair.b)});
                pairs.insert({static_cast<size_t>(std::min(pair.a, pair.b)), static_cast<size_t>(std::max(pair.a, pair.b))});
            }
            if (value->completeness == "complete" && pairs.size() != input->body_count * (input->body_count - 1) / 2)
                return reject_c1(state, EAB2_INVALID_INPUT, "pairs", "complete list must include all body pairs");
        }
        Object created; created.type = EAB2_HANDLE_ASSEMBLY2; created.assembly = std::move(value);
        *output = add_object(state, context, std::move(created));
        return EAB2_OK;
    });
}
extern "C" EAB2_API eab2_call_status eab2_assembly2_destroy(eab2_context context, eab2_assembly2 assembly) {
    return destroy_object(context, assembly, EAB2_HANDLE_ASSEMBLY2);
}
extern "C" EAB2_API eab2_call_status eab2_contact_set2_destroy(eab2_context context, eab2_contact_set2 contacts) {
    return destroy_object(context, contacts, EAB2_HANDLE_CONTACTSET2);
}
extern "C" EAB2_API eab2_call_status eab2_assemble_contact_set2(eab2_context context,
    eab2_assembly2 assembly, eab2_contact_set2* output) {
    if (!output) return EAB2_INVALID_INPUT;
    *output = {};
    return c1_call(context, [&](ContextState& state) {
        const auto* found = object(state, context, assembly, EAB2_HANDLE_ASSEMBLY2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "assembly", "invalid assembly handle");
        Object created; created.type = EAB2_HANDLE_CONTACTSET2;
        created.contacts = std::make_unique<eab2::contact::ContactSet2>(eab2::contact::assemble_contact_set2(*found->assembly));
        *output = add_object(state, context, std::move(created));
        return EAB2_OK;
    });
}
extern "C" EAB2_API eab2_call_status eab2_contact_set2_export_exact(eab2_context context,
    eab2_contact_set2 contacts, eab2_exact_result* output) {
    return c1_call(context, [&](ContextState& state) {
        const auto* found = object(state, context, contacts, EAB2_HANDLE_CONTACTSET2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "contacts", "invalid contact set handle");
        const auto status = header(output);
        if (status != EAB2_OK) return reject_c1(state, status, "output", "invalid exact result header");
        return save_exact(state, context, eab2::contact::export_exact(*found->contacts),
            l1_math(found->contacts->mathematical_status), output);
    });
}
extern "C" EAB2_API eab2_call_status eab2_query_lock(eab2_context context, eab2_assembly2 assembly,
    const eab2_lock2_input* input, eab2_exact_result* output) {
    return c1_call(context, [&](ContextState& state) {
        const auto* found = object(state, context, assembly, EAB2_HANDLE_ASSEMBLY2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "assembly", "invalid assembly handle");
        const auto in_status = header(input), out_status = header(output);
        if (in_status != EAB2_OK) return reject_c1(state, in_status, "input", "invalid lock header");
        if (out_status != EAB2_OK) return reject_c1(state, out_status, "output", "invalid exact result header");
        if (input->moving_index >= found->assembly->bodies.size() || input->neighbor_stride != sizeof(uint64_t) ||
            !c1_extent(input->neighbor_count, input->neighbor_stride) || (input->neighbor_count && !input->neighbors))
            return reject_c1(state, EAB2_INVALID_INPUT, "neighbors", "invalid moving body/neighbors descriptor");
        if (input->neighbor_count > state.limits.max_elements)
            return reject_c1(state, EAB2_RESOURCE_LIMIT, "neighbors", "neighbor count limit exceeded");
        std::vector<eab2::geometry2::Body> neighbors;
        for (uint64_t i = 0; i < input->neighbor_count; ++i) {
            const auto at = input->neighbors[i];
            if (at >= found->assembly->bodies.size() || at == input->moving_index)
                return reject_c1(state, EAB2_INVALID_INPUT, "neighbors", "invalid explicit neighbor index", i);
            neighbors.push_back(found->assembly->bodies[static_cast<size_t>(at)].geometry);
        }
        const auto result = eab2::contact::query_lock(found->assembly->bodies[static_cast<size_t>(input->moving_index)].geometry,
            neighbors, state.limits);
        return save_exact(state, context, eab2::contact::export_exact(result), l1_math(result.mathematical_status), output);
    });
}
extern "C" EAB2_API eab2_call_status eab2_first_order_mobility(eab2_context context,
    eab2_contact_set2 contacts, eab2_exact_result* output) {
    return c1_call(context, [&](ContextState& state) {
        const auto* found = object(state, context, contacts, EAB2_HANDLE_CONTACTSET2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "contacts", "invalid contact set handle");
        const auto status = header(output);
        if (status != EAB2_OK) return reject_c1(state, status, "output", "invalid exact result header");
        const auto result = eab2::contact::first_order_mobility(*found->contacts);
        return save_exact(state, context, eab2::contact::export_exact(result), l1_math(result.mathematical_status), output);
    });
}

#ifdef EAB2_ENABLE_TEST_API
#include <thread>
#include <chrono>
extern "C" EAB2_API eab2_call_status eab2_opt_solve_exact(eab2_context context,
    const eab2_opt_input* input, eab2_exact_result* output) {
    return c1_call(context, [&](ContextState& state) {
        const auto in_status = header(input), out_status = header(output);
        if (in_status != EAB2_OK) return reject_c1(state, in_status, "input", "invalid opt header");
        if (out_status != EAB2_OK) return reject_c1(state, out_status, "output", "invalid exact result header");
        if (input->sense > 1 || input->reserved || !input->max_pivots ||
            input->max_pivots > std::numeric_limits<size_t>::max() ||
            input->value_stride != sizeof(eab2_text) || !c1_extent(input->value_count, input->value_stride) ||
            (input->value_count && !input->values))
            return reject_c1(state, EAB2_INVALID_INPUT, "opt", "invalid sense, pivot limit, pointer or stride");
        if (input->rows > 1024 || input->columns > 4096 || input->value_count > 65536 ||
            input->rows * input->columns + input->rows + input->columns > 65536)
            return reject_c1(state, EAB2_RESOURCE_LIMIT, "opt", "LP shape work limit exceeded");
        if (input->value_count != input->rows * input->columns + input->rows + input->columns)
            return reject_c1(state, EAB2_INVALID_INPUT, "values", "LP exact array shape mismatch");
        uint64_t parse_work = 0;
        for (uint64_t i = 0; i < input->value_count; ++i) {
            const auto text = input->values[i];
            if (!text.data || !text.length)
                return reject_c1(state, EAB2_INVALID_INPUT, "values", "empty exact LP value", i);
            if (text.length > 4096 || text.length * text.length > UINT64_C(67108864) - parse_work)
                return reject_c1(state, EAB2_RESOURCE_LIMIT, "values", "LP parsing work limit exceeded", i);
            parse_work += text.length * text.length;
        }
        size_t at = 0;
        auto parse = [&]() {
            const auto text = input->values[at++];
            return eab2::numeric::parse_rational(std::string(text.data, static_cast<size_t>(text.length)));
        };
        eab2::opt::Matrix A(static_cast<size_t>(input->rows), eab2::opt::Vector(static_cast<size_t>(input->columns)));
        eab2::opt::Vector b(static_cast<size_t>(input->rows)), c(static_cast<size_t>(input->columns));
        for (auto& row : A) for (auto& value : row) value = parse();
        for (auto& value : b) value = parse();
        for (auto& value : c) value = parse();
        eab2::opt::Options options; options.max_pivots = static_cast<size_t>(input->max_pivots);
        const auto result = input->sense ? eab2::opt::maximize(A, b, c, options) : eab2::opt::solve(A, b, c, options);
        const auto math = result.status == eab2::opt::Status::optimal ? EAB2_MATH_VALUE :
            result.status == eab2::opt::Status::infeasible ? EAB2_MATH_INFEASIBLE : EAB2_MATH_UNBOUNDED;
        return save_exact(state, context, eab2::opt::export_exact(result, input->sense != 0), math, output);
    });
}
extern "C" EAB2_API eab2_call_status eab2_test_context_rendezvous(eab2_context context) {
    return c1_call(context, [&](ContextState&) -> uint32_t {
        static std::atomic<unsigned> arrivals{0}, round{0};
        static std::atomic<bool> timed_out{false};
        if (timed_out.load()) return EAB2_CANCELLED;
        const auto current = round.load();
        if (arrivals.fetch_add(1) == 1) {
            arrivals.store(0); round.fetch_add(1); return EAB2_OK;
        }
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(10);
        while (round.load() == current) {
            if (std::chrono::steady_clock::now() >= deadline) {
                timed_out.store(true); return EAB2_CANCELLED;
            }
            std::this_thread::yield();
        }
        return EAB2_OK;
    });
}
#endif

namespace {
uint32_t l3_math(const std::optional<std::string>& name) {
    if (name && *name == "INFEASIBLE") return EAB2_MATH_INFEASIBLE;
    if (name && *name == "UNBOUNDED") return EAB2_MATH_UNBOUNDED;
    return l1_math(name);
}
uint32_t l3_status(const std::string& name) {
    if (name == "INVALID_INPUT") return EAB2_INVALID_INPUT;
    if (name == "UNSUPPORTED") return EAB2_UNSUPPORTED;
    if (name == "RESOURCE_LIMIT") return EAB2_RESOURCE_LIMIT;
    if (name == "CONSTRUCTION_RANGE") return EAB2_CONSTRUCTION_RANGE;
    if (name == "CANCELLED") return EAB2_CANCELLED;
    return EAB2_INTERNAL_ERROR;
}
uint32_t decode_parameter(ContextState& state, uint64_t bits, const char* field,
                          eab2::exact::Rational& value) {
    try { value = eab2::numeric::decode_binary64(bits); }
    catch (const eab2::numeric::Error& error) {
        return reject_c1(state, error.code, field, error.what());
    }
    if (value < eab2::exact::Rational(0))
        return reject_c1(state, EAB2_INVALID_INPUT, field, "parameter must be nonnegative");
    return EAB2_OK;
}
uint32_t decode_loads(ContextState& state, const eab2::contact::ContactSet2& contacts,
                      uint64_t count, uint64_t stride, const eab2_body_load2* input,
                      eab2::statics::Loads2& loads) {
    if (stride != sizeof(eab2_body_load2) || !c1_extent(count, stride) ||
        count != contacts.assembly.bodies.size() || (count && !input))
        return reject_c1(state, EAB2_INVALID_INPUT, "loads", "load count/stride/pointer must match assembly bodies");
    if (count > state.limits.max_elements)
        return reject_c1(state, EAB2_RESOURCE_LIMIT, "loads", "load count limit exceeded");
    loads.resize(static_cast<size_t>(count));
    for (size_t i = 0; i < loads.size(); ++i) {
        try {
            for (size_t k = 0; k < 3; ++k) {
                loads[i].dead[k] = eab2::numeric::decode_binary64(input[i].dead_bits[k]);
                loads[i].live[k] = eab2::numeric::decode_binary64(input[i].live_bits[k]);
            }
        } catch (const eab2::numeric::Error& error) {
            return reject_c1(state, error.code, "loads", error.what(), i);
        }
    }
    return EAB2_OK;
}
}
extern "C" EAB2_API eab2_call_status eab2_get_c3l3_abi_info(eab2_c3l3_abi_info* info) {
    const auto status = header(info);
    if (status != EAB2_OK) return status;
    if (info->reserved) return EAB2_INVALID_INPUT;
    *info = {sizeof(eab2_c3l3_abi_info), EAB2_ABI_VERSION, sizeof(eab2_body_load2),
        sizeof(eab2_limit2_input), sizeof(eab2_critical_parameter_input), 0};
    return EAB2_OK;
}
extern "C" EAB2_API eab2_call_status eab2_solve_limit2(eab2_context context,
    eab2_contact_set2 contacts, const eab2_limit2_input* input, eab2_exact_result* output) {
    return c1_call(context, [&](ContextState& state) {
        const auto* found = object(state, context, contacts, EAB2_HANDLE_CONTACTSET2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "contacts", "invalid contact set handle");
        const auto in_status = header(input), out_status = header(output);
        if (in_status != EAB2_OK) return reject_c1(state, in_status, "input", "invalid limit input header");
        if (out_status != EAB2_OK) return reject_c1(state, out_status, "output", "invalid exact result header");
        eab2::exact::Rational mu;
        const auto parameter_status = decode_parameter(state, input->mu_bits, "mu", mu);
        if (parameter_status != EAB2_OK) return parameter_status;
        eab2::statics::Loads2 loads;
        const auto decoded = decode_loads(state, *found->contacts, input->body_count, input->body_stride, input->loads, loads);
        if (decoded != EAB2_OK) return decoded;
        auto result = eab2::statics::limit_load_ideal_exact_2d(*found->contacts, loads, mu);
        if (result.call_status != "OK")
            return reject_c1(state, l3_status(result.call_status), "limit", result.reason.value_or("limit query failed").c_str());
        auto json = eab2::statics::export_exact(result);
        const auto math = l3_math(result.mathematical_status);
        auto snapshot = std::make_shared<eab2::contact::ContactSet2>(*found->contacts);
        return save_exact(state, context, std::move(json), math, output,
            std::make_unique<eab2::statics::LimitResult2>(std::move(result)), {}, std::move(snapshot));
    });
}
extern "C" EAB2_API eab2_call_status eab2_critical_parameter(eab2_context context,
    eab2_contact_set2 contacts, const eab2_critical_parameter_input* input, eab2_exact_result* output) {
    return c1_call(context, [&](ContextState& state) {
        const auto* found = object(state, context, contacts, EAB2_HANDLE_CONTACTSET2);
        if (!found) return reject_c1(state, EAB2_INVALID_HANDLE, "contacts", "invalid contact set handle");
        const auto in_status = header(input), out_status = header(output);
        if (in_status != EAB2_OK) return reject_c1(state, in_status, "input", "invalid critical input header");
        if (out_status != EAB2_OK) return reject_c1(state, out_status, "output", "invalid exact result header");
        if (input->reserved)
            return reject_c1(state, EAB2_INVALID_INPUT, "reserved", "critical reserved must be zero");
        if (input->parameter != EAB2_PARAMETER_MU)
            return reject_c1(state, EAB2_UNSUPPORTED, "parameter", "only mu has the required cone nesting");
        if (input->max_steps > 4096)
            return reject_c1(state, EAB2_RESOURCE_LIMIT, "max_steps", "binary64 refinement limit exceeded");
        eab2::exact::Rational mu_max;
        const auto parameter_status = decode_parameter(state, input->mu_max_bits, "mu_max", mu_max);
        if (parameter_status != EAB2_OK) return parameter_status;
        eab2::statics::Loads2 loads;
        const auto decoded = decode_loads(state, *found->contacts, input->body_count, input->body_stride, input->loads, loads);
        if (decoded != EAB2_OK) return decoded;
        auto result = eab2::statics::critical_parameter(*found->contacts, loads, mu_max, static_cast<size_t>(input->max_steps));
        result.original_mu_max_bits = input->mu_max_bits;
        if (result.call_status != "OK")
            return reject_c1(state, l3_status(result.call_status), "critical", result.reason.value_or("critical query failed").c_str());
        auto json = eab2::statics::export_exact(result);
        const auto math = l3_math(result.mathematical_status);
        auto snapshot = std::make_shared<eab2::contact::ContactSet2>(*found->contacts);
        return save_exact(state, context, std::move(json), math, output, {},
            std::make_unique<eab2::statics::CriticalParameter2>(std::move(result)), std::move(snapshot));
    });
}

namespace {
uint64_t l4_product(uint64_t a, uint64_t b) {
    if (b && a > std::numeric_limits<size_t>::max() / b)
        throw eab2::numeric::Error(EAB2_INVALID_INPUT, "sensitivity dimension multiplication overflow");
    return a * b;
}
struct SeedTextBudget {
    uint64_t bytes = 0, square = 0;
    std::string take(const eab2_string& value, bool utf8, const char* field, uint64_t index) {
        if (!value.data || !value.length)
            throw IndexedInputError(EAB2_INVALID_INPUT, field, index, "empty sensitivity text");
        if (value.length > 4096 || value.length > UINT64_C(4194304) - bytes ||
            value.length * value.length > UINT64_C(67108864) - square)
            throw IndexedInputError(EAB2_RESOURCE_LIMIT, field, index, "sensitivity aggregate text parsing budget");
        bytes += value.length; square += value.length * value.length;
        std::string text(value.data, static_cast<size_t>(value.length));
        if (utf8 && (!valid_utf8(text) || text.find('\0') != std::string::npos))
            throw IndexedInputError(EAB2_INVALID_INPUT, field, index, "invalid sensitivity UTF-8 text");
        return text;
    }
};
void l4_array(const eab2_string_array& values, uint64_t expected, size_t limit, const char* field, uint64_t index = UINT64_MAX) {
    if (values.value_count != expected || values.value_stride != sizeof(eab2_string) ||
        !c1_extent(values.value_count, values.value_stride) || (expected && !values.values))
        throw IndexedInputError(EAB2_INVALID_INPUT, field, index, "sensitivity array count/stride/pointer mismatch");
    if (expected > limit)
        throw IndexedInputError(EAB2_RESOURCE_LIMIT, field, index, "sensitivity array element budget");
}
std::string l4_quote(const std::string& text) {
    static constexpr char hex[] = "0123456789abcdef";
    std::string out = "\"";
    for (const unsigned char value : text) {
        if (value == '"' || value == '\\') { out += '\\'; out += static_cast<char>(value); }
        else if (value < 32) { out += "\\u00"; out += hex[value >> 4]; out += hex[value & 15]; }
        else out += static_cast<char>(value);
    }
    return out + '"';
}
std::string l4_vector(const eab2::statics::Vector& values) {
    std::string out = "[";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) out += ',';
        out += l4_quote(values[i].canonical());
    }
    return out + ']';
}
std::string l4_seed(const std::optional<eab2::statics::LimitSeed2>& seed) {
    if (!seed) return "null";
    std::string out = "{\"parameter\":" + l4_quote(seed->parameter) + ",\"dA\":[";
    for (size_t i = 0; i < seed->dA.size(); ++i) {
        if (i) out += ',';
        out += l4_vector(seed->dA[i]);
    }
    return out + "],\"db\":" + l4_vector(seed->db) + ",\"dc\":" + l4_vector(seed->dc) + '}';
}
}
extern "C" EAB2_API eab2_call_status eab2_get_c3l4_abi_info(eab2_c3l4_abi_info* info) {
    const auto status = header(info);
    if (status != EAB2_OK) return status;
    if (info->reserved || info->reserved2) return EAB2_INVALID_INPUT;
    *info = {sizeof(eab2_c3l4_abi_info), EAB2_ABI_VERSION, sizeof(eab2_string_array),
        sizeof(eab2_sensitivity_vertex2), sizeof(eab2_sensitivity_channel2),
        sizeof(eab2_sensitivity2_input), 0, 0};
    return EAB2_OK;
}
extern "C" EAB2_API eab2_call_status eab2_evaluate_sensitivity2(eab2_context context,
    eab2_result base_result, const eab2_sensitivity2_input* input, eab2_exact_result* output) {
    return c1_call(context, [&](ContextState& state) {
        const auto* found = object(state, context, base_result, EAB2_HANDLE_RESULT);
        if (!found || (!found->limit_result && !found->critical_result) || !found->sensitivity_contacts)
            return reject_c1(state, EAB2_INVALID_HANDLE, "base_result", "retained typed L3 result required");
        const auto in_status = header(input), out_status = header(output);
        if (in_status != EAB2_OK) return reject_c1(state, in_status, "input", "invalid sensitivity input header");
        if (out_status != EAB2_OK) return reject_c1(state, out_status, "output", "invalid sensitivity output header");
        const auto& contacts = *found->sensitivity_contacts;
        const uint64_t p = input->parameter_count, b = input->body_count, v = input->vertex_count;
        uint64_t expected_vertices = 0;
        for (const auto& body : contacts.assembly.bodies) expected_vertices += body.geometry.vertices.size();
        if (!p || input->output_count != 1 || input->channel_count != p ||
            b != contacts.assembly.bodies.size() || v != expected_vertices ||
            input->channel_stride != sizeof(eab2_sensitivity_channel2) ||
            !c1_extent(p, input->channel_stride) || !input->channels ||
            input->vertex_stride != sizeof(eab2_sensitivity_vertex2) ||
            !c1_extent(v, input->vertex_stride) || (v && !input->vertex_ids))
            return reject_c1(state, EAB2_INVALID_INPUT, "dimensions", "invalid parameter/output/channel/body/vertex dimensions");
        // Reject the independent channel budget before any dimension product
        // or array access; a huge but extent-valid p must retain named detail.
        if (p > 1024 || p > state.limits.max_elements)
            return reject_c1(state, EAB2_RESOURCE_LIMIT, "parameter_count", "sensitivity parameter/channel budget exceeded");
        const auto pv2 = l4_product(l4_product(p, v), 2);
        const auto pb3 = l4_product(l4_product(p, b), 3);
        const auto pb2 = l4_product(l4_product(p, b), 2);
        l4_array(input->body_ids, b, state.limits.max_elements, "body_ids");
        l4_array(input->vertices, pv2, state.limits.max_elements, "vertices");
        l4_array(input->dead, pb3, state.limits.max_elements, "dead");
        l4_array(input->live, pb3, state.limits.max_elements, "live");
        l4_array(input->dof_anchor, pb2, state.limits.max_elements, "dof_anchor");
        l4_array(input->mu, p, state.limits.max_elements, "mu");
        if (pv2 > state.limits.max_elements - p || pb3 > (state.limits.max_elements - p - pv2) / 2 ||
            pb2 > state.limits.max_elements - p - pv2 - 2 * pb3)
            return reject_c1(state, EAB2_RESOURCE_LIMIT, "seeds", "sensitivity aggregate element/channel budget");

        SeedTextBudget budget;
        std::vector<std::string> ids;
        for (uint64_t i = 0; i < b; ++i) ids.push_back(budget.take(input->body_ids.values[i], true, "body_ids", i));
        std::vector<std::pair<std::string, size_t>> vertices;
        for (uint64_t i = 0; i < v; ++i) {
            const auto& vertex = input->vertex_ids[i];
            if (vertex.vertex_id > std::numeric_limits<size_t>::max())
                return reject_c1(state, EAB2_INVALID_INPUT, "vertex_ids", "vertex ID outside platform range", i);
            vertices.emplace_back(budget.take(vertex.body_id, true, "vertex_ids", i), static_cast<size_t>(vertex.vertex_id));
        }
        auto parse = [&](const eab2_string_array& values, uint64_t at) {
            const char* field = &values == &input->mu ? "mu" : &values == &input->vertices ? "vertices" :
                &values == &input->dead ? "dead" : &values == &input->live ? "live" : "dof_anchor";
            const auto text = budget.take(values.values[at], false, field, at);
            try { return eab2::numeric::parse_rational(text); }
            catch (const eab2::exact::ResourceLimit& error) { throw IndexedInputError(EAB2_RESOURCE_LIMIT, field, at, error.what()); }
            catch (const eab2::numeric::Error& error) { throw IndexedInputError(error.code, field, at, error.what()); }
            catch (const std::invalid_argument& error) { throw IndexedInputError(EAB2_INVALID_INPUT, field, at, error.what()); }
        };
        std::vector<std::string> expected_ids;
        std::vector<std::pair<std::string, size_t>> expected_vertex_ids;
        std::map<std::pair<std::string, size_t>, eab2::statics::Point> raw_points;
        for (const auto& body : contacts.assembly.bodies) {
            expected_ids.push_back(body.body_id);
            for (size_t k = 0; k < body.geometry.vertices.size(); ++k) {
                const auto id = std::make_pair(body.body_id, body.geometry.original_vertex_ids[k]);
                expected_vertex_ids.push_back(id); raw_points[id] = body.geometry.vertices[k];
            }
        }
        std::sort(expected_ids.begin(), expected_ids.end()); std::sort(expected_vertex_ids.begin(), expected_vertex_ids.end());
        for (size_t k = 0; k < ids.size(); ++k) if (ids[k] != expected_ids[k])
            return reject_c1(state, EAB2_INVALID_INPUT, "body_ids", "body identity order mismatch", k);
        for (size_t k = 0; k < vertices.size(); ++k) if (vertices[k] != expected_vertex_ids[k])
            return reject_c1(state, EAB2_INVALID_INPUT, "vertex_ids", "original vertex identity order mismatch", k);
        std::vector<eab2::statics::GeometrySeed2> seeds;
        std::vector<eab2::statics::SensitivityOptions2> options;
        std::set<std::string> parameters;
        for (uint64_t channel = 0; channel < p; ++channel) {
            const auto& source = input->channels[channel];
            const auto status = header(&source);
            if (status != EAB2_OK) return reject_c1(state, status, "channels", "invalid sensitivity channel header", channel);
            if (source.positive_direction_valid > 1 || source.negative_direction_valid > 1)
                return reject_c1(state, EAB2_INVALID_INPUT, "channels", "direction flags must be zero or one", channel);
            eab2::statics::GeometrySeed2 seed;
            eab2::statics::SensitivityOptions2 option;
            seed.parameter = option.parameter = budget.take(source.parameter, true, "parameter", channel);
            if (!parameters.insert(seed.parameter).second)
                return reject_c1(state, EAB2_INVALID_INPUT, "parameter", "duplicate parameter name", channel);
            option.positive_direction_valid = source.positive_direction_valid != 0;
            option.negative_direction_valid = source.negative_direction_valid != 0;
            l4_array(source.validity_conditions, source.validity_conditions.value_count, state.limits.max_elements, "validity_conditions", channel);
            l4_array(source.tied_labels, source.tied_labels.value_count, state.limits.max_elements, "tied_labels", channel);
            for (uint64_t i = 0; i < source.validity_conditions.value_count; ++i)
                option.validity_conditions.push_back(budget.take(source.validity_conditions.values[i], true, "validity_conditions", i));
            for (uint64_t i = 0; i < source.tied_labels.value_count; ++i)
                option.tied_labels.emplace_back(budget.take(source.tied_labels.values[i], true, "tied_labels", i));
            seed.mu = parse(input->mu, channel);
            if (found->critical_result && seed.mu != eab2::exact::Rational(0))
                return reject_c1(state, EAB2_INVALID_INPUT, "mu", "threshold query does not admit a friction seed", channel);
            for (uint64_t i = 0; i < v; ++i) seed.vertices.push_back({vertices[i].first, vertices[i].second,
                {parse(input->vertices, (channel * v + i) * 2), parse(input->vertices, (channel * v + i) * 2 + 1)}});
            for (uint64_t i = 0; i < b; ++i) {
                eab2::statics::BodySeed2 body;
                body.body_id = ids[i];
                for (uint64_t k = 0; k < 3; ++k) {
                    body.dead[k] = parse(input->dead, (channel * b + i) * 3 + k);
                    body.live[k] = parse(input->live, (channel * b + i) * 3 + k);
                }
                for (uint64_t k = 0; k < 2; ++k) body.dof_anchor[k] = parse(input->dof_anchor, (channel * b + i) * 2 + k);
                seed.bodies.push_back(std::move(body));
            }
            std::map<eab2::statics::Point, eab2::statics::Point> shared;
            for (size_t k = 0; k < seed.vertices.size(); ++k) {
                const auto& item = seed.vertices[k]; const auto point = raw_points.at({item.body_id, item.vertex_id});
                const auto [at, inserted] = shared.emplace(point, item.derivative);
                if (!inserted && at->second != item.derivative)
                    return reject_c1(state, EAB2_INVALID_INPUT, "vertices", "geometry jet breaks a shared vertex", (channel * v + k) * 2);
            }
            try { eab2::statics::validate_geometry_seed2(contacts, seed); }
            catch (const std::invalid_argument& error) { return reject_c1(state, EAB2_INVALID_INPUT, "vertices", error.what(), channel); }
            seeds.push_back(std::move(seed)); options.push_back(std::move(option));
        }
        const eab2::statics::LimitProblem2* problem = nullptr;
        if (found->limit_result && found->limit_result->problem) problem = &*found->limit_result->problem;
        if (found->critical_result && found->critical_result->threshold_certificate &&
            found->critical_result->threshold_certificate->problem)
            problem = &*found->critical_result->threshold_certificate->problem;
        std::string json = "{\"sensitivity_model\":\"ideal_exact_2d\",\"parameter_count\":" + std::to_string(p) +
            ",\"output_count\":1,\"channel_count\":" + std::to_string(p) +
            ",\"jacobian_layout\":\"output_major_channel_minor\",\"jacobian_shape\":[1," + std::to_string(p) + "],\"channels\":[";
        std::string jacobian = "[";
        for (size_t i = 0; i < seeds.size(); ++i) {
            std::optional<eab2::statics::LimitSeed2> derived, mu_seed;
            if (problem) {
                derived = eab2::statics::propagate_geometry_seed2(*problem, seeds[i]);
                if (found->critical_result) {
                    auto unit_mu = seeds[i]; unit_mu.parameter = "mu"; unit_mu.mu = 1;
                    for (auto& vertex : unit_mu.vertices) vertex.derivative = {0, 0};
                    for (auto& body : unit_mu.bodies) { body.dead = {0, 0, 0}; body.live = {0, 0, 0}; body.dof_anchor = {0, 0}; }
                    mu_seed = eab2::statics::propagate_geometry_seed2(*problem, unit_mu);
                }
            }
            const auto result = found->limit_result ?
                eab2::statics::evaluate_sensitivity2(*found->limit_result, derived, options[i]) :
                eab2::statics::evaluate_sensitivity2(*found->critical_result, derived, mu_seed, options[i]);
            if (result.call_status != "OK")
                return reject_c1(state, l3_status(result.call_status), "sensitivity", result.reason.value_or("sensitivity failed").c_str(), i);
            if (i) { json += ','; jacobian += ','; }
            json += "{\"parameter\":" + l4_quote(seeds[i].parameter) + ",\"result\":" + eab2::statics::export_exact(result) +
                ",\"derived_seed\":" + l4_seed(derived) + ",\"threshold_mu_seed\":" + l4_seed(mu_seed) + '}';
            jacobian += result.differentiability == "smooth" && result.quality == "exact_jet" && result.directional_derivative ?
                l4_quote(result.directional_derivative->canonical()) : "null";
        }
        json += "],\"jacobian\":" + jacobian + "]}";
        const auto math = found->limit_result ? l3_math(found->limit_result->mathematical_status) : l3_math(found->critical_result->mathematical_status);
        return save_exact(state, context, std::move(json), math, output);
    });
}
