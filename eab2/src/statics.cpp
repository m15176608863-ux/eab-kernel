#include "statics.hpp"
#include <algorithm>
#include <limits>
#include <sstream>

namespace eab2::statics {
namespace {
Vector project(const contact::Body2& body, const Wrench& wrench) {
    if (body.boundary_type == "FIXED_BODY") return {};
    const auto offset = geometry2::sub(body.dof_anchor, body.reference_point);
    const Wrench moved{wrench[0], wrench[1],
        wrench[2] - geometry2::cross(offset, {wrench[0], wrench[1]})};
    Vector out;
    for (std::size_t k = 0; k < 3; ++k) {
        if (body.dof_mask[k] != 0 && body.dof_mask[k] != 1)
            throw std::invalid_argument("invalid DOF mask");
        if (body.dof_mask[k]) out.push_back(moved[k]);
    }
    return out;
}
Rational dot(const Vector& a, const Vector& b) {
    if (a.size() != b.size()) throw std::logic_error("statics vector width mismatch");
    Rational value;
    for (std::size_t i = 0; i < a.size(); ++i) value = value + a[i] * b[i];
    return value;
}
std::string quote(const std::string& text) {
    std::string out = "\"";
    const char* hex = "0123456789abcdef";
    for (const unsigned char ch : text) {
        if (ch == '\\' || ch == '"') { out += '\\'; out += static_cast<char>(ch); }
        else if (ch < 32) { out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15]; }
        else out += static_cast<char>(ch);
    }
    return out + '"';
}
template<class Range, class Encode> std::string array(const Range& values, Encode encode) {
    std::string out = "[";
    bool first = true;
    for (const auto& value : values) { if (!first) out += ','; first = false; out += encode(value); }
    return out + ']';
}
std::string rational(const Rational& q) { return quote(q.canonical()); }
std::string vector(const Vector& v) { return array(v, rational); }
std::string point(const Point& p) { return array(p, rational); }
std::string matrix(const Matrix& m) { return array(m, vector); }
std::string optional_string(const std::optional<std::string>& value) { return value ? quote(*value) : "null"; }
std::string optional_vector(const std::optional<Vector>& value) { return value ? vector(*value) : "null"; }
} // namespace

LimitProblem2 build_limit_problem2(const contact::ContactSet2& contacts,
                                  const Loads2& loads, const Rational& mu) {
    const auto& assembly = contacts.assembly;
    geometry2::GeometryWorkScope work(assembly.limits);
    exact::IntegerLimitScope integers(assembly.limits.max_integer_bits);
    if (mu < Rational(0)) throw std::invalid_argument("mu must be nonnegative");
    if (assembly.profile != "profile1") throw std::invalid_argument("unsupported profile");
    if (loads.size() != assembly.bodies.size()) throw std::invalid_argument("loads body count mismatch");
    if (contacts.status != "RESOLVED" || !contacts.unresolved.empty())
        throw std::invalid_argument("contact_set_unresolved");
    if (contacts.completeness != "complete") throw std::invalid_argument("completeness_unknown");
    LimitProblem2 problem;
    problem.mu = mu;
    problem.contact_set = contacts;
    problem.loads = loads;
    for (const auto& body : assembly.bodies) {
        problem.reference_points.push_back(body.reference_point);
        problem.dof_anchors.push_back(body.dof_anchor);
        if (body.boundary_type == "FIXED_BODY") continue;
        for (std::size_t k = 0; k < 3; ++k) {
            if (body.dof_mask[k] != 0 && body.dof_mask[k] != 1)
                throw std::invalid_argument("invalid DOF mask");
            if (body.dof_mask[k]) problem.row_labels.emplace_back(body.body_id, k);
        }
    }
    if (contacts.constraints.size() > (std::numeric_limits<std::size_t>::max() - 1) / 2)
        throw exact::ResourceLimit("statics column count overflow");
    const std::size_t rows = problem.row_labels.size(), columns = contacts.constraints.size() * 2 + 1;
    work.check_size(rows);
    work.check_size(columns);
    if (rows && columns > work.limits.max_elements / rows)
        throw exact::ResourceLimit("statics matrix element limit exceeded");
    problem.A.assign(rows, Vector(columns));
    problem.c.assign(columns, Rational(0));
    problem.c.back() = Rational(1);
    std::size_t column = 0;
    // Only retained L1 constraints enter statics. REDUNDANT_PROVED true corner
    // contacts have a kinematic proof but must never supply extra force rays.
    for (const auto& contact : contacts.constraints) {
        if (contact.a >= assembly.bodies.size() || contact.b >= assembly.bodies.size() || contact.a == contact.b)
            throw std::invalid_argument("invalid contact body indices");
        const Point normal{-contact.tangent[1], contact.tangent[0]};
        if (normal == Point{0, 0}) throw std::invalid_argument("zero contact direction");
        for (const int sign : {-1, 1}) {
            const Point force{normal[0] + Rational(sign) * mu * contact.tangent[0],
                              normal[1] + Rational(sign) * mu * contact.tangent[1]};
            std::size_t row = 0;
            for (std::size_t i = 0; i < assembly.bodies.size(); ++i) {
                const auto& body = assembly.bodies[i];
                const Rational sense(static_cast<int>(i == contact.a) - static_cast<int>(i == contact.b));
                const Point arm = geometry2::sub(contact.point, body.reference_point);
                // Construct the moment exactly about the frozen reference, then
                // transform its virtual work to the physical anchor coordinates.
                const Wrench wrench{sense * force[0], sense * force[1], sense * geometry2::cross(arm, force)};
                for (const auto& v : project(body, wrench)) { work.step(); problem.A[row++][column] = v; }
            }
            problem.column_labels.push_back({contact.label, sign});
            ++column;
        }
    }
    std::size_t row = 0;
    for (std::size_t i = 0; i < assembly.bodies.size(); ++i) {
        const auto live = project(assembly.bodies[i], loads[i].live);
        const auto dead = project(assembly.bodies[i], loads[i].dead);
        for (std::size_t k = 0; k < live.size(); ++k) {
            problem.A[row++][column] = live[k];
            problem.b.push_back(-dead[k]);
        }
    }
    problem.column_labels.push_back({std::nullopt, 1});
    return problem;
}

LimitResult2 solve_limit_problem2(const LimitProblem2& problem, const opt::Options& options) {
    geometry2::GeometryWorkScope work(problem.contact_set.assembly.limits);
    exact::IntegerLimitScope integers(problem.contact_set.assembly.limits.max_integer_bits);
    const auto solved = opt::maximize(problem.A, problem.b, problem.c, options);
    if (!opt::verify_certificate(problem.A, problem.b, problem.c, solved, true))
        throw std::logic_error("statics original-model certificate failed");
    LimitResult2 result;
    result.problem = problem;
    result.basis = solved.basis;
    result.stats = solved.stats;
    if (std::any_of(problem.contact_set.points.begin(), problem.contact_set.points.end(),
        [](const auto& point) { return point.fp_type == "REDUNDANT_PROVED"; }))
        result.validity_conditions.push_back("true_vv_excluded_from_statics");
    if (solved.status == opt::Status::optimal) {
        result.mathematical_status = "OPTIMAL";
        result.display_status = "EXACT";
        result.exact_value = solved.exact_objective;
        result.exact_x = solved.exact_x;
        result.exact_y = solved.exact_y;
        result.mechanism = solved.exact_y;
    } else if (solved.status == opt::Status::unbounded) {
        result.mathematical_status = "UNBOUNDED";
        result.feasible_point = solved.exact_x;
        result.improving_ray = solved.exact_ray;
    } else {
        result.mathematical_status = "INFEASIBLE";
        Vector y = solved.exact_y;
        const auto normalization = dot(problem.b, y);
        if (normalization <= Rational(0)) throw std::logic_error("invalid statics Farkas normalization");
        for (auto& entry : y) entry = entry / normalization;
        result.farkas = std::move(y);
    }
    return result;
}

LimitResult2 limit_load_ideal_exact_2d(const contact::ContactSet2& contacts,
                                    const Loads2& loads, const Rational& mu,
                                    const opt::Options& options) {
    LimitResult2 result;
    if (contacts.call_status != "OK") {
        result.call_status = contacts.call_status;
        result.reason = contacts.reason;
        return result;
    }
    if (contacts.status != "RESOLVED" || !contacts.unresolved.empty()) {
        result.mathematical_status = contacts.unresolved.empty() ? contacts.mathematical_status : "MECHANICAL_UNRESOLVED";
        result.reason = "contact_set_unresolved";
        return result;
    }
    if (contacts.completeness != "complete") {
        result.mathematical_status = "UNPROVED";
        result.reason = "completeness_unknown";
        return result;
    }
    try {
        return solve_limit_problem2(build_limit_problem2(contacts, loads, mu), options);
    } catch (const std::invalid_argument& error) {
        result.call_status = "INVALID_INPUT";
        result.reason = error.what();
        return result;
    }
}
LimitResult2 limit_load_ideal_exact_2d(const contact::Assembly2& assembly,
                                    const Loads2& loads, const Rational& mu,
                                    const opt::Options& options) {
    return limit_load_ideal_exact_2d(contact::assemble_contact_set2(assembly), loads, mu, options);
}

std::string export_exact(const ColumnLabel2& label) {
    if (!label.contact) return "[\"alpha\"," + std::to_string(label.sign) + ']';
    const auto& c = *label.contact;
    return "[[" + quote(c.a) + ',' + quote(c.b) + ',' + point(c.point) + ',' + quote(c.edge_body) +
        ",[" + std::to_string(c.edge[0]) + ',' + std::to_string(c.edge[1]) + "]]," + std::to_string(label.sign) + ']';
}
std::string export_exact(const LimitProblem2& p) {
    return "{\"A\":" + matrix(p.A) + ",\"b\":" + vector(p.b) + ",\"c\":" + vector(p.c) +
        ",\"row_labels\":" + array(p.row_labels, [](const auto& row) { return '[' + quote(row.first) + ',' + std::to_string(row.second) + ']'; }) +
        ",\"column_labels\":" + array(p.column_labels, [](const auto& label) { return export_exact(label); }) +
        ",\"reference_points\":" + array(p.reference_points, point) + ",\"dof_anchors\":" + array(p.dof_anchors, point) +
        ",\"mu\":" + rational(p.mu) + ",\"profile\":" + quote(p.profile) + ",\"sensitivity_model\":" + quote(p.sensitivity_model) + '}';
}
std::string export_exact(const LimitResult2& r) {
    std::ostringstream out;
    out << "{\"call_status\":" << quote(r.call_status) << ",\"mathematical_status\":" << optional_string(r.mathematical_status)
        << ",\"display_status\":" << quote(r.display_status) << ",\"exact_value\":" << (r.exact_value ? rational(*r.exact_value) : "null")
        << ",\"exact_x\":" << optional_vector(r.exact_x) << ",\"exact_y\":" << optional_vector(r.exact_y)
        << ",\"feasible_point\":" << optional_vector(r.feasible_point) << ",\"improving_ray\":" << optional_vector(r.improving_ray)
        << ",\"farkas\":" << optional_vector(r.farkas) << ",\"mechanism\":" << optional_vector(r.mechanism)
        << ",\"problem\":" << (r.problem ? export_exact(*r.problem) : "null")
        << ",\"reason\":" << optional_string(r.reason)
        << ",\"basis\":" << array(r.basis, [](std::size_t i) { return std::to_string(i); })
        << ",\"sensitivity_model\":" << quote(r.sensitivity_model)
        << ",\"validity_conditions\":" << array(r.validity_conditions, quote) << '}';
    return out.str();
}
} // namespace eab2::statics
