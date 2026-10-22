#if defined(__AVX__)
#error eab2 controlled sources require the x64 SSE2 compilation target
#endif
#include "eab2/c_api.h"
#include "fp_contract.hpp"
#include "build_identity.hpp"
#include "geometry2.hpp"
#include "numeric.hpp"

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
struct Object {
    uint64_t generation = 0;
    uint32_t type = 0;
    uint32_t flags = 0;
    std::unique_ptr<eab2::geometry2::Body> body;
    std::unique_ptr<eab2::geometry2::Entrance> entrance;
    std::unique_ptr<std::string> json;
};
struct ContextState {
    uint64_t generation = 0;
    ErrorState error;
    eab2::geometry2::GeometryLimits limits;
    std::vector<Object> objects;
};
std::mutex registry_mutex;
std::unordered_map<uint64_t, std::unique_ptr<ContextState>> registry;
uint64_t next_id = 1;
uint64_t next_generation = 1;
uint64_t generation() {
    if (next_generation == UINT64_MAX) throw eab2::numeric::Error(EAB2_RESOURCE_LIMIT, "handle generation exhausted");
    return next_generation++;
}

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
    return found != registry.end() && found->second && found->second->generation == token.generation
        ? found->second.get() : nullptr;
}
template<class T> uint32_t header(const T* value) noexcept {
    if (!value || value->struct_size != sizeof(T)) return EAB2_INVALID_INPUT;
    return value->abi_version == EAB2_ABI_VERSION ? EAB2_OK : EAB2_UNSUPPORTED;
}
uint64_t capabilities() noexcept {
    uint64_t result = EAB2_CAP_CONTEXT | EAB2_CAP_BODY2 | EAB2_CAP_ENTRANCE2 |
        EAB2_CAP_QUERY2 | EAB2_CAP_EXPORT_EXACT | EAB2_CAP_LOCAL2 | EAB2_CAP_LIMITS2;
#ifdef EAB2_ENABLE_TEST_API
    result |= EAB2_CAP_TEST_NUMERIC | EAB2_CAP_TEST_EXACT2;
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
        std::lock_guard lock(registry_mutex);
        if (!lookup(context)) return EAB2_INVALID_HANDLE;
        registry[context.id].reset();
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
template<class Function> uint32_t c1_call(eab2_context context, Function function) noexcept {
    try {
        std::lock_guard lock(registry_mutex);
        auto* state = lookup(context);
        if (!state) return EAB2_INVALID_HANDLE;
        state->error = {};
        const auto fp_status = eab2::fp::self_test();
        if (fp_status != EAB2_OK)
            return reject_c1(*state, fp_status, "environment", "floating-point contract failed");
        eab2::exact::IntegerLimitScope integer_scope(state->limits.max_integer_bits);
        eab2::geometry2::GeometryWorkScope work_scope(state->limits);
        return function(*state);
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
    });
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
    });
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
                result.bits = eab2::numeric::evaluate(in.operation, in.encoding, values,
                    (in.flags & EAB2_NUMERIC_ALLOW_UNDERFLOW) != 0, &result.underflow_zero);
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
