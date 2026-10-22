#include "critical.hpp"
#include "numeric.hpp"
#include <algorithm>
#include <iostream>
#include <stdexcept>

using namespace eab2::statics;
namespace ct = eab2::contact;
namespace geom = eab2::geometry2;
namespace detail = eab2::statics::critical_detail;
namespace {
int checks = 0;
void require(bool condition, const char* message) { ++checks; if (!condition) throw std::runtime_error(message); }
Rational q(int n, int d = 1) { return Rational(eab2::exact::Int(n), eab2::exact::Int(d)); }
struct Model { ct::Assembly2 assembly; Loads2 loads; };
ct::Assembly2 assembly(std::vector<ct::Body2> bodies) {
    ct::Assembly2 out;
    out.bodies = std::move(bodies); out.completeness = "complete"; out.pairs.emplace();
    for (std::size_t i = 0; i < out.bodies.size(); ++i)
        for (std::size_t j = i + 1; j < out.bodies.size(); ++j) out.pairs->push_back({i, j});
    return out;
}
Model beam(Rational t, Rational h, const std::string& orientation) {
    std::vector<Rational> slopes;
    if (orientation == "unreversed") slopes = {t, -t, t, -t};
    else if (orientation == "reverse_i1") slopes = {-t, -t, t, -t};
    else slopes = {-t, -t, t, t};
    std::vector<std::array<Point, 2>> faces{{Point{-5, 0}, Point{-5, h}}};
    for (std::size_t i = 0; i < slopes.size(); ++i) {
        const auto x = Rational(static_cast<int>(-3 + 2 * static_cast<int>(i)));
        faces.push_back({Point{x - slopes[i] * h / Rational(2), 0}, Point{x + slopes[i] * h / Rational(2), h}});
    }
    faces.push_back({Point{5, 0}, Point{5, h}});
    const Point origin{q(5, 8), q(-3, 8)};
    std::vector<ct::Body2> bodies;
    Loads2 loads(5);
    for (std::size_t i = 0; i < 5; ++i) {
        const bool fixed = i == 0 || i == 4;
        bodies.emplace_back("block_" + std::to_string(i + 1),
            geom::Body({faces[i][0], faces[i + 1][0], faces[i + 1][1], faces[i][1]}), origin,
            fixed ? "FIXED_BODY" : "", fixed ? std::array<int, 3>{0, 0, 0} : std::array<int, 3>{1, 1, 1}, origin);
    }
    loads[2].live = {0, -1, origin[0]};
    return {assembly(std::move(bodies)), std::move(loads)};
}
CriticalParameter2 run(const Model& model, const Rational& max = Rational(1), std::size_t steps = 16) {
    return critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, max, steps);
}
void verify(const LimitResult2& result) {
    require(result.problem.has_value(), "endpoint retains original LP");
    const auto& p = *result.problem;
    eab2::opt::Result witness;
    if (result.mathematical_status == "OPTIMAL") {
        witness.status = eab2::opt::Status::optimal;
        witness.exact_x = *result.exact_x; witness.exact_y = *result.exact_y; witness.exact_objective = result.exact_value;
    } else if (result.mathematical_status == "UNBOUNDED") {
        witness.status = eab2::opt::Status::unbounded;
        witness.exact_x = *result.feasible_point; witness.exact_ray = *result.improving_ray;
        require(witness.exact_ray.back() == Rational(1), "upper alpha ray normalization");
    } else {
        require(result.mathematical_status == "INFEASIBLE", "endpoint mathematical state");
        witness.status = eab2::opt::Status::infeasible; witness.exact_y = *result.farkas;
    }
    require(eab2::opt::verify_certificate(p.A, p.b, p.c, witness, true), "exact endpoint mathematical certificate");
}
void verify(const CriticalParameter2& answer) {
    require(answer.call_status == "OK", "critical call valid");
    if (answer.mu_lo) require(detail::is_binary64(*answer.mu_lo), "lower endpoint binary64");
    if (answer.mu_hi) require(detail::is_binary64(*answer.mu_hi), "upper endpoint binary64");
    if (answer.lower_certificate) verify(*answer.lower_certificate);
    if (answer.upper_certificate) verify(*answer.upper_certificate);
    if (answer.threshold_certificate) verify(*answer.threshold_certificate);
    if (answer.exact_threshold && answer.mu_hi)
        require(*answer.mu_lo <= *answer.exact_threshold && *answer.exact_threshold <= *answer.mu_hi, "threshold in bracket");
}
void binary_grid() {
    using eab2::exact::Int;
    const auto denorm = Rational(Int(1), Int(1) << 1074);
    require(detail::is_binary64(denorm), "smallest subnormal representable");
    require(!detail::is_binary64(denorm / Rational(2)), "below subnormal not representable");
    require(!detail::is_binary64(q(1, 3)), "nonbinary rational not representable");
    require(!detail::is_binary64(Rational(Int(1) << 1024)), "overflow not representable");
    require(!detail::binary_midpoint(Rational(0), denorm), "adjacent zero/subnormal has no interior");
    require(detail::binary_midpoint(Rational(0), denorm * Rational(2)) == denorm, "single subnormal interior");
    const auto one_next = Rational(1) + Rational(Int(1), Int(1) << 52);
    require(!detail::binary_midpoint(Rational(1), one_next), "54-bit midpoint not accepted");
    require(detail::binary_midpoint(Rational(1), one_next + Rational(Int(1), Int(1) << 52)) == one_next, "grid interior exact");
    const auto largest = Rational((Int(1) << 53) - Int(1)) * Rational(Int(1) << 971);
    const auto large_unit = Rational(Int(1) << 971);
    require(detail::is_binary64(largest), "largest finite binary64 representable");
    require(!detail::binary_midpoint(largest - large_unit, largest), "largest adjacent pair has no interior");
    require(detail::binary_midpoint(largest - Rational(2) * large_unit, largest) == largest - large_unit, "largest grid midpoint exact");
    // Exact bit decoding is the independent oracle for grid adjacency,
    // including subnormal/normal and normal exponent transitions.
    for (const std::uint64_t bits : {UINT64_C(0), UINT64_C(1), UINT64_C(0x000fffffffffffff),
        UINT64_C(0x0010000000000000), UINT64_C(0x3fefffffffffffff),
        UINT64_C(0x3ff0000000000000), UINT64_C(0x7feffffffffffffe)}) {
        const auto lo = eab2::numeric::decode_binary64(bits);
        const auto hi = eab2::numeric::decode_binary64(bits + 1);
        require(detail::is_binary64(lo) && detail::is_binary64(hi), "decoded finite endpoint exact");
        require(!detail::binary_midpoint(lo, hi), "adjacent binary64 pair has no rational-grid interior");
    }
    const auto candidate = detail::rational_candidate2(q(229, 1000), q(23, 100));
    require(candidate == q(11, 48), "continued fraction rational candidate");
}
void polynomial_guards() {
    // Independent factored scalar oracle: (x-1/8)(x-1/4), positive at midpoint
    // but negative inside [0,1]. The production Sturm proof must reject it.
    CriticalBasis2 branch{"improving_ray", {0}, 1, {1}, {{q(1, 32), q(-3, 8), 1}}, {}, 1, {q(21, 32)}};
    require(!detail::branch_signs2(branch, 0, 1), "interior numerator roots rejected despite positive midpoint");
    require(!detail::branch_signs2(std::nullopt, 0, 0), "absent branch not degenerate proof");
    require(detail::branch_signs2(branch, 1, 1)->empty(), "equal interval is empty proof");
    branch.numerators = {{0, 0, 1}};
    auto signs = detail::branch_signs2(branch, 0, 1);
    require(signs && (*signs)[1].endpoint_orders[0] == 2 && (*signs)[1].value == q(1, 4), "endpoint multiplicity retained");
    branch.determinant = {q(-1, 4), 1};
    require(!detail::branch_signs2(branch, 0, 1), "interior denominator root rejected");
    branch.determinant = {1}; branch.numerators = {{-1}};
    require(!detail::branch_signs2(branch, 0, 1), "negative continuation ratio rejected");
    branch.numerators = {{q(1, 16), q(-1, 2), 1}};
    require(!detail::branch_signs2(branch, 0, 1), "even interior zero conservatively rejected");
    // x^2(1-x)^2 has only double endpoint zeros, unlike an interior zero.
    branch.numerators = {{0, 0, 1, -2, 1}};
    signs = detail::branch_signs2(branch, 0, 1);
    require(signs && (*signs)[1].endpoint_orders == std::array<std::size_t, 2>{2, 2}, "both endpoint double roots factored exactly");
    branch.numerators = {{0}};
    signs = detail::branch_signs2(branch, 0, 1);
    require(signs && (*signs)[1].value == Rational(0) && (*signs)[1].endpoint_orders == std::array<std::size_t, 2>{0, 0}, "zero numerator is an identically active constraint");
    branch.determinant = {0};
    require(!detail::branch_signs2(branch, 0, 1), "identically singular denominator has no continuation");
    LimitProblem2 p;
    p.A = {{1, 1}}; p.b = {1}; p.c = {1, 2}; p.column_labels.resize(2);
    auto wrong = solve_limit_problem2(p);
    wrong.exact_y = Vector{1};
    const PolynomialMatrix2 matrix{{Polynomial2{1}, Polynomial2{1}}};
    require(!detail::mechanism_basis2(wrong, matrix), "negative reduced cost cannot certify mechanism branch");
}
void threshold_contracts() {
    struct Case { Rational t, h, truth; std::string orientation; bool attained; };
    // Oracle values are independent hand-substituted G1 closed forms, not LP
    // candidate values: t-(h/2)(1+t*t), t (open), and t (closed).
    for (const auto& c : std::vector<Case>{
        {q(1, 3), q(3, 16), q(11, 48), "koureas", true},
        {q(3, 16), 1, q(3, 16), "unreversed", false},
        {q(5, 16), 1, q(5, 16), "reverse_i1", true},
        {q(1, 8), q(1, 16), q(191, 2048), "koureas", true},
        {0, 1, 0, "koureas", false},
        {q(1, 4), 1, 0, "koureas", true}}) {
        const auto result = run(beam(c.t, c.h, c.orientation));
        verify(result);
        require(result.exact_threshold == c.truth && result.attained == c.attained, "G1 exact threshold and openness");
        if (c.truth != Rational(0)) require(!result.critical_polynomials.empty(), "threshold basis polynomials retained");
        if (!c.attained) require(result.threshold_certificate->mathematical_status == "OPTIMAL", "open threshold itself bounded");
        if (c.truth == q(11, 48)) require(!detail::is_binary64(*result.exact_threshold), "rational-only threshold separate from endpoints");
    }
    const auto low_budget = run(beam(q(3, 16), 1, "unreversed"), 1, 1);
    verify(low_budget);
    require(low_budget.mu_hi == q(1, 2), "one-step bracket upper endpoint");
    require(!low_budget.exact_threshold && !low_budget.attained,
        "unreversed_open_requires_above: endpoint states cannot certify an open threshold");
    // Acceptance MAJOR-1: these wide Koureas brackets contain a different
    // polynomial root above the true threshold. An unbounded candidate is
    // not a threshold unless the lower-side bounded continuation is proved.
    // Independent hand-substituted truths: t-(h/2)*(1+t*t).
    const auto koureas_wide_four_steps = run(beam(q(3, 32), q(1, 16), "koureas"), q(3, 4), 4);
    verify(koureas_wide_four_steps);
    require(koureas_wide_four_steps.mu_lo == q(3, 64) && koureas_wide_four_steps.mu_hi == q(3, 32),
        "koureas_wide_four_steps: exact binary64 bracket");
    require(*koureas_wide_four_steps.mu_lo < q(2039, 32768) && q(2039, 32768) < *koureas_wide_four_steps.mu_hi,
        "koureas_wide_four_steps: independent truth lies strictly inside bracket");
    require(!koureas_wide_four_steps.exact_threshold && !koureas_wide_four_steps.attained,
        "koureas_wide_four_steps_requires_below: unbounded endpoint is not a closed threshold");
    require(!koureas_wide_four_steps.threshold_certificate && !koureas_wide_four_steps.threshold_proof
            && !koureas_wide_four_steps.threshold_proof_reason,
        "koureas_wide_four_steps: unproved threshold has no threshold proof fields");
    const auto koureas_wide_one_step = run(beam(q(3, 8), q(1, 4), "koureas"), q(3, 8), 1);
    verify(koureas_wide_one_step);
    require(koureas_wide_one_step.mu_lo == q(3, 16) && koureas_wide_one_step.mu_hi == q(3, 8),
        "koureas_wide_one_step: exact binary64 bracket");
    require(*koureas_wide_one_step.mu_lo < q(119, 512) && q(119, 512) < *koureas_wide_one_step.mu_hi,
        "koureas_wide_one_step: independent truth lies strictly inside bracket");
    require(!koureas_wide_one_step.exact_threshold && !koureas_wide_one_step.attained,
        "koureas_wide_one_step_requires_below: unbounded endpoint is not a closed threshold");
    require(!koureas_wide_one_step.threshold_certificate && !koureas_wide_one_step.threshold_proof
            && !koureas_wide_one_step.threshold_proof_reason,
        "koureas_wide_one_step: unproved threshold has no threshold proof fields");
    const auto zero_budget = run(beam(q(3, 16), 1, "unreversed"), 1, 0);
    verify(zero_budget);
    require(zero_budget.mu_lo == Rational(0) && zero_budget.mu_hi == Rational(1), "zero steps retains original endpoint bracket");
    require(zero_budget.bisection_termination == "iteration_limit" && !zero_budget.exact_threshold && !zero_budget.attained,
        "zero steps cannot guess a root from endpoint states");
    const auto zero_domain = run(beam(0, 1, "koureas"), 0, 0);
    verify(zero_domain);
    require(zero_domain.reason == "bounded_on_domain" && zero_domain.queries == 1 && !zero_domain.mu_hi,
        "zero-width domain with bounded zero does not imply open zero threshold");
    const auto zero_unbounded = run(beam(q(1, 4), 1, "koureas"), 0, 0);
    verify(zero_unbounded);
    require(zero_unbounded.exact_threshold == Rational(0) && zero_unbounded.attained == true && zero_unbounded.queries == 1,
        "zero-width domain with unbounded zero certifies attained boundary");
    require(!zero_unbounded.lower_certificate && !zero_unbounded.bisection_termination && !zero_unbounded.threshold_proof_reason,
        "zero already unbounded does not fabricate a lower mechanism or continuation");
    const auto domain = run(beam(q(3, 16), 1, "unreversed"), q(1, 8));
    verify(domain);
    require(!domain.mu_hi && domain.reason == "bounded_on_domain" && !domain.attained, "bounded within domain only");
    using eab2::exact::Int;
    const auto tiny = run(beam(0, 1, "koureas"), Rational(Int(1), Int(1) << 1073), 1);
    verify(tiny);
    require(tiny.reason == "input_resolution_limit" && tiny.bisection_termination == tiny.reason, "last-step resolution reason preserved");
    require(tiny.threshold_proof_reason == "exact_basis_continuation", "proof reason is separate field");
    require(tiny.exact_threshold == Rational(0) && tiny.attained == false, "open zero with subnormal domain");
    require(tiny.mu_hi == Rational(Int(1), Int(1) << 1074), "smallest subnormal upper bracket");
    const auto contacts = ct::assemble_contact_set2(beam(q(1, 4), 1, "koureas").assembly);
    const auto loads = beam(q(1, 4), 1, "koureas").loads;
    require(critical_parameter(contacts, loads, 1, 16, "height").call_status == "UNSUPPORTED", "only mu is monotone");
    require(critical_parameter(contacts, loads, q(1, 3)).call_status == "INVALID_INPUT", "nonbinary64 search endpoint rejected");
    require(critical_parameter(contacts, loads, -1).call_status == "INVALID_INPUT", "negative search endpoint rejected");
    const auto wire = export_exact(tiny);
    require(wire.find("\"mu_hi_bits\":\"0000000000000001\"") != std::string::npos, "binary64 endpoint exact wire bits");
    require(wire.find("\"threshold_proof_reason\":\"exact_basis_continuation\"") != std::string::npos, "proof reason serialized independently");
}
Model transform(Model model, const Rational& scale, const Point& translation, const Rational& a, const Rational& b) {
    require(a * a + b * b == Rational(1), "exact orthogonal rotation");
    auto rotate = [&](const Point& p) -> Point { return {a * p[0] - b * p[1], b * p[0] + a * p[1]}; };
    auto map = [&](const Point& p) -> Point { return geom::add(geom::mul(rotate(p), scale), translation); };
    for (auto& body : model.assembly.bodies) {
        geom::Polygon vertices;
        for (const auto& p : body.geometry.vertices) vertices.push_back(map(p));
        body.geometry = geom::Body(vertices);
        body.reference_point = map(body.reference_point); body.dof_anchor = map(body.dof_anchor);
    }
    for (auto& load : model.loads) for (auto* w : {&load.dead, &load.live}) {
        const auto force = rotate({(*w)[0], (*w)[1]});
        *w = {force[0], force[1], scale * (*w)[2]};
    }
    return model;
}
void invariant_thresholds() {
    // Reproducible random rational rotations use the Pythagorean
    // parameterization; no trigonometric rounding enters the exact oracle.
    std::uint32_t seed = UINT32_C(0xc3c30003);
    auto next = [&]() { seed = UINT32_C(1664525) * seed + UINT32_C(1013904223); return seed; };
    for (const auto& orientation : {std::string("unreversed"), std::string("reverse_i1")}) {
        const auto base = beam(q(3, 16), 1, orientation);
        for (const auto& shift : std::vector<Rational>{0, 1000, 100000, 1000000}) {
            const auto scale = shift == Rational(1000000) ? q(1, 1024) : Rational(8);
            const int u = 2 + static_cast<int>(next() % 11), v = 1 + static_cast<int>(next() % static_cast<std::uint32_t>(u - 1));
            const auto a = q(u * u - v * v, u * u + v * v), b = q(2 * u * v, u * u + v * v);
            const auto moved = transform(base, scale, {shift, -shift}, a, b);
            const auto result = run(moved, 1, 8);
            verify(result);
            require(result.exact_threshold == q(3, 16), "critical invariant under exact rigid motion and units");
            require(result.attained == (orientation == "reverse_i1"), "openness invariant under exact rigid motion");
        }
    }
    auto model = beam(q(3, 16), 1, "unreversed");
    // A reference-frame change does not change the physical DOF anchor. Loads
    // must change their moment by -(new_origin-old_origin) cross force.
    for (std::size_t i = 0; i < model.assembly.bodies.size(); ++i) {
        auto& body = model.assembly.bodies[i];
        const Point offset{q(13, 7), q(-5, 3)};
        body.reference_point = geom::add(body.reference_point, offset);
        for (auto* w : {&model.loads[i].dead, &model.loads[i].live})
            (*w)[2] = (*w)[2] - geom::cross(offset, Point{(*w)[0], (*w)[1]});
    }
    const auto reframed = run(model, 1, 8);
    verify(reframed);
    require(reframed.exact_threshold == q(3, 16) && reframed.attained == false, "reference and wrench reparameterization invariance");
}
void unavailable_contracts() {
    ct::Body2 free("free", geom::Body({{0, 0}, {1, 0}, {1, 1}, {0, 1}}));
    Model infeasible{assembly({free}), Loads2(1)};
    infeasible.loads[0].dead = {1, 0, 0}; infeasible.loads[0].live = {0, -1, 0};
    const auto result = run(infeasible, 2);
    verify(result);
    require(result.mathematical_status == "INFEASIBLE" && result.reason == "infeasible_on_domain", "infeasible domain remains infeasible");
    require(!result.mu_hi && result.lower_certificate->farkas, "infeasible domain Farkas not finite capacity");
    ct::Body2 corner("corner", geom::Body({{1, 1}, {2, 1}, {2, 2}, {1, 2}}), {0, 0}, "FIXED_BODY", {0, 0, 0});
    const auto unresolved = run({assembly({free, corner}), Loads2(2)});
    require(unresolved.mathematical_status == "UNPROVED" && unresolved.reason == "contact_set_unresolved", "unresolved contact not fabricated bracket");
    auto unknown = beam(q(1, 4), 1, "koureas");
    unknown.assembly.completeness = "completeness_unknown"; unknown.assembly.pairs.reset();
    const auto no_domain = run(unknown);
    require(no_domain.mathematical_status == "UNPROVED" && !no_domain.mu_lo && !no_domain.mu_hi, "missing completeness has no endpoints");
}
void private_integer_budget() {
    const auto model = beam(q(3, 16), 1, "unreversed");
    auto contacts = ct::assemble_contact_set2(model.assembly);
    contacts.assembly.limits.max_integer_bits = 16;
    // The input exists before the call. The private critical entry must apply
    // the configured integer budget while checking its binary64 domain, not
    // only inside later LP calls or the public ABI wrapper.
    const auto huge_domain = Rational(eab2::exact::Int(1) << 200);
    auto unresolved = contacts;
    unresolved.status = "MECHANICAL_UNRESOLVED";
    unresolved.mathematical_status = "MECHANICAL_UNRESOLVED";
    bool limited = false;
    // No LP is reachable for this unresolved contact set: a failure cannot be
    // accidentally attributed to the nested LP's separate integer scope.
    try { (void)critical_parameter(unresolved, model.loads, huge_domain, 0); }
    catch (const eab2::exact::ResourceLimit&) { limited = true; }
    require(limited, "private critical input arithmetic observes integer budget");
    require(eab2::exact::integer_limit_bits == 0, "private critical restores caller integer budget after failure");
    contacts.assembly.limits.max_integer_bits = 128;
    const auto low = limit_load_ideal_exact_2d(contacts, model.loads, 0);
    const auto high = limit_load_ideal_exact_2d(contacts, model.loads, 1);
    require(low.mathematical_status == "OPTIMAL" && high.mathematical_status == "UNBOUNDED",
        "polynomial budget example has certified endpoint LPs within budget");
    limited = false;
    try { (void)critical_parameter(contacts, model.loads, 1, 0); }
    catch (const eab2::exact::ResourceLimit&) { limited = true; }
    require(limited, "private critical polynomial continuation retains integer budget after endpoint LP scopes");
    require(eab2::exact::integer_limit_bits == 0, "polynomial budget failure restores caller state");
}
} // namespace
int main() {
    try {
        binary_grid(); polynomial_guards(); threshold_contracts(); invariant_thresholds(); unavailable_contracts(); private_integer_budget();
        std::cout << "C3L3_CRITICAL_OK checks=" << checks << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "C3L3_CRITICAL_FAIL checks=" << checks << " reason=" << error.what() << '\n';
        return 1;
    }
}
