#include "statics.hpp"
#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <tuple>

using namespace eab2::statics;
namespace contact = eab2::contact;
namespace geom = eab2::geometry2;
namespace {
int checks = 0;
void require(bool condition, const char* message) { ++checks; if (!condition) throw std::runtime_error(message); }
Rational q(std::int64_t n, std::int64_t d = 1) { return Rational(eab2::exact::Int(n), eab2::exact::Int(d)); }
Rational dot(const Vector& a, const Vector& b) {
    require(a.size() == b.size(), "certificate vector dimensions");
    Rational out;
    for (std::size_t i = 0; i < a.size(); ++i) out = out + a[i] * b[i];
    return out;
}
void verify(const LimitResult2& r) {
    require(r.call_status == "OK" && r.problem.has_value(), "exact LP result available");
    const auto& p = *r.problem;
    if (r.mathematical_status == "OPTIMAL") {
        require(r.exact_x && r.exact_y && r.exact_value && r.mechanism, "optimum primal dual and mechanism");
        for (const auto& x : *r.exact_x) require(x >= Rational(0), "primal nonnegative");
        for (std::size_t i = 0; i < p.b.size(); ++i) require(dot(p.A[i], *r.exact_x) == p.b[i], "primal equilibrium");
        for (std::size_t j = 0; j < p.c.size(); ++j) {
            Rational column;
            for (std::size_t i = 0; i < p.b.size(); ++i) column = column + p.A[i][j] * (*r.exact_y)[i];
            require(column >= p.c[j], "dual mechanism inequalities including drive at least one");
        }
        require(dot(p.c, *r.exact_x) == *r.exact_value && dot(p.b, *r.exact_y) == *r.exact_value, "strong duality");
        require(r.mechanism == r.exact_y, "dual is anchor-coordinate mechanism");
        require(!r.feasible_point && !r.improving_ray && !r.farkas, "optimum status payload separation");
    } else if (r.mathematical_status == "UNBOUNDED") {
        require(r.feasible_point && r.improving_ray && !r.exact_value && !r.exact_y, "unbounded is not a finite capacity");
        for (const auto& v : *r.feasible_point) require(v >= Rational(0), "feasible point nonnegative");
        for (const auto& v : *r.improving_ray) require(v >= Rational(0), "improving ray nonnegative");
        for (std::size_t i = 0; i < p.b.size(); ++i) {
            require(dot(p.A[i], *r.feasible_point) == p.b[i], "unbounded feasible point equilibrium");
            require(dot(p.A[i], *r.improving_ray) == Rational(0), "unbounded ray equilibrium");
        }
        require(dot(p.c, *r.improving_ray) == Rational(1), "objective ray normalized to one");
    } else {
        require(r.mathematical_status == "INFEASIBLE" && r.farkas, "infeasible Farkas supplied");
        require(dot(p.b, *r.farkas) == Rational(1), "Farkas normalized to one");
        for (std::size_t j = 0; j < p.c.size(); ++j) {
            Rational value;
            for (std::size_t i = 0; i < p.b.size(); ++i) value = value + p.A[i][j] * (*r.farkas)[i];
            require(value <= Rational(0), "Farkas column sign");
        }
    }
}
geom::Polygon rectangle(Rational x0, Rational x1, Rational y0 = 0, Rational y1 = 1) {
    return {{x0, y0}, {x1, y0}, {x1, y1}, {x0, y1}};
}
contact::Assembly2 assembly(std::vector<contact::Body2> bodies) {
    contact::Assembly2 a;
    a.bodies = std::move(bodies);
    a.completeness = "complete";
    a.pairs.emplace();
    for (std::size_t i = 0; i < a.bodies.size(); ++i)
        for (std::size_t j = i + 1; j < a.bodies.size(); ++j) a.pairs->push_back({i, j});
    return a;
}
contact::Body2 body(std::string id, geom::Polygon polygon, bool fixed = false, Point origin = {q(5, 8), q(-3, 8)}) {
    return contact::Body2(std::move(id), geom::Body(polygon), origin, fixed ? "FIXED_BODY" : "",
        fixed ? std::array<int, 3>{0, 0, 0} : std::array<int, 3>{1, 1, 1}, origin);
}
struct Model { contact::Assembly2 assembly; Loads2 loads; };
Model beam(int n = 3, Rational h = 1, Rational pressure = 1,
           std::array<int, 3> mask = {1, 0, 0}, std::optional<Point> anchor = {},
           Point origin = {q(5, 8), q(-3, 8)}) {
    Model model;
    std::vector<contact::Body2> bodies{body("left", rectangle(-1, 0, 0, h), true, origin)};
    model.loads.resize(static_cast<std::size_t>(n) + 2);
    for (int i = 0; i < n; ++i) {
        bodies.push_back(body("block_" + std::to_string(i), rectangle(i, i + 1, 0, h), false, origin));
        if (i == n / 2) model.loads[i + 1].live = {0, -1, -(q(n, 2) - origin[0])};
    }
    bodies.emplace_back("plate", geom::Body(rectangle(n, n + 1, 0, h)), origin,
        "FORCE_CONTROLLED_PLATE", mask, anchor.value_or(Point{n, h / q(2)}));
    model.loads.back().dead = {-pressure, 0, (h / q(2) - origin[1]) * pressure};
    model.assembly = assembly(std::move(bodies));
    return model;
}
contact::ContactSet2 hand_endpoints(const Model& model, int n, Rational h) {
    contact::ContactSet2 cs;
    cs.assembly = model.assembly;
    cs.status = "RESOLVED"; cs.mathematical_status = "RESOLVED"; cs.completeness = "complete";
    for (int face = 0; face <= n; ++face)
        for (const Rational y : {q(0), h}) {
            const std::size_t a = static_cast<std::size_t>(face + 1), b = static_cast<std::size_t>(face);
            const Point p{face, y};
            contact::ContactLabel2 label{cs.assembly.bodies[a].body_id, cs.assembly.bodies[b].body_id,
                p, cs.assembly.bodies[a].body_id, {0, 3}};
            cs.constraints.push_back({a, b, p, {0, -h}, {}, label});
        }
    return cs;
}
void g5_closed_form_and_masks() {
    // Primary oracle: elementary horizontal/vertical force balance and endpoint
    // moment capacity. Handwritten endpoints do not use production geometry.
    struct Case { int n; Rational mu, h, pressure; };
    for (const Case c : {Case{3, 0, 1, 1}, Case{3, q(1, 4), 1, 1}, Case{3, 2, 1, 1},
                         Case{5, 2, 1, 1}, Case{7, 2, 1, 1}, Case{3, q(3, 8), q(3, 2), q(5, 4)}}) {
        const auto m = beam(c.n, c.h, c.pressure);
        const auto independent = limit_load_ideal_exact_2d(hand_endpoints(m, c.n, c.h), m.loads, c.mu);
        const auto actual = limit_load_ideal_exact_2d(m.assembly, m.loads, c.mu);
        const auto expected = std::min(q(2) * c.mu * c.pressure, q(4) * c.pressure * c.h / q(c.n - 1));
        require(actual.exact_value == expected && independent.exact_value == expected, "G5 closed form and C3-L1 regression d");
        verify(independent); verify(actual);
    }
    for (const auto mask : {std::array<int, 3>{1, 1, 0}, std::array<int, 3>{1, 0, 1}}) {
        const auto m = beam(3, 1, 1, mask);
        const auto r = limit_load_ideal_exact_2d(m.assembly, m.loads, q(2));
        require(r.exact_value == (mask[1] ? q(2, 3) : q(4, 3)), "released plate physical-anchor counterexample");
        verify(r);
    }
    for (const Point origin : {Point{0, 0}, Point{q(5, 8), q(-3, 8)}, Point{131072, -1024}}) {
        const auto m = beam(3, 1, 1, {1, 0, 1}, Point{0, 0}, origin);
        const auto r = limit_load_ideal_exact_2d(m.assembly, m.loads, q(2));
        require(r.exact_value == q(1, 3), "reference change transforms contact and load moments together");
        verify(r);
    }
}
void matrix_and_certificates() {
    const auto m = beam(3, 2);
    const auto p = build_limit_problem2(hand_endpoints(m, 3, 2), m.loads, q(1, 4));
    require(p.A[0][0] == q(2) && p.A[0][1] == q(2), "unnormalized original tangent gives normal magnitude two");
    require(p.A[1][0] == q(1, 2) && p.A[1][1] == q(-1, 2), "g minus then g plus sign convention");
    require(p.A[4].back() == q(-1) && p.A[5].back() == -q(7, 8), "live load alpha column frozen-origin moment");
    const std::size_t interface = 4;
    for (std::size_t k = 0; k < 3; ++k)
        require(p.A[k][interface] == -p.A[k + 3][interface], "same frozen frame action reaction exact opposites");
    for (const auto& raw : std::vector<std::tuple<Matrix, Vector, Vector, std::string>>{
             {{{1, -1}}, {2}, {0, 1}, "UNBOUNDED"},
             {{{1, 1}}, {-3}, {0, 1}, "INFEASIBLE"},
             {{}, {}, {1}, "UNBOUNDED"}}) {
        LimitProblem2 problem;
        problem.A = std::get<0>(raw); problem.b = std::get<1>(raw); problem.c = std::get<2>(raw);
        const auto r = solve_limit_problem2(problem);
        require(r.mathematical_status == std::get<3>(raw), "all exact LP statuses");
        verify(r);
    }
    auto cs = hand_endpoints(m, 3, 2);
    cs.status = "MECHANICAL_UNRESOLVED"; cs.mathematical_status = "MECHANICAL_UNRESOLVED";
    auto r = limit_load_ideal_exact_2d(cs, m.loads, q(0));
    require(r.mathematical_status == "MECHANICAL_UNRESOLVED" && !r.problem && !r.exact_value, "unresolved is not zero capacity");
    cs.status = "RESOLVED"; cs.mathematical_status = "RESOLVED"; cs.completeness = "completeness_unknown";
    r = limit_load_ideal_exact_2d(cs, m.loads, q(0));
    require(r.mathematical_status == "UNPROVED" && !r.problem, "unknown completeness refuses assembly");
    cs.completeness = "complete";
    require(limit_load_ideal_exact_2d(cs, m.loads, q(-1)).call_status == "INVALID_INPUT", "negative friction rejected");
    require(limit_load_ideal_exact_2d(cs, Loads2{}, q(0)).call_status == "INVALID_INPUT", "load count rejected");
    const auto redundant = assembly({body("A", rectangle(0, 1)), body("B", rectangle(1, 2, 1, 2), true),
                                    body("C", rectangle(1, 2), true)});
    const auto contact_set = contact::assemble_contact_set2(redundant);
    const auto excluded = limit_load_ideal_exact_2d(contact_set, Loads2(3), q(1, 4));
    require(excluded.problem && excluded.problem->c.size() == 2 * contact_set.constraints.size() + 1 &&
        std::none_of(contact_set.constraints.begin(), contact_set.constraints.end(), [](const auto& c) {
            return (c.a == 0 && c.b == 1) || (c.a == 1 && c.b == 0);
        }), "true corner redundancy adds no force column");
    require(excluded.validity_conditions == std::vector<std::string>{"true_vv_excluded_from_statics"}, "true corner exclusion disclosed");
    require(export_exact(excluded).find("\"problem\":{") != std::string::npos, "exact problem export available");
}
Model floor_model() {
    Model m;
    // A non-axis-centered body has elementary friction capacity mu*dead = 1/4;
    // its contact span is wide enough that tipping is not the active bound.
    m.assembly = assembly({body("moving", rectangle(-2, 3, 0, 2)), body("floor", rectangle(-3, 4, -1, 0), true)});
    m.loads.resize(2);
    const auto o = m.assembly.bodies[0].reference_point;
    m.loads[0].dead = {0, -1, o[0]};
    m.loads[0].live = {1, 0, -(q(1) - o[1])};
    return m;
}
Model five_block_chain(const std::string& orientation) {
    const Rational t = q(1, 4), h = q(1);
    const Point origin{q(5, 8), q(-3, 8)};
    std::array<Rational, 4> slopes{-t, -t, t, t};
    if (orientation == "unreversed") slopes = {t, -t, t, -t};
    if (orientation == "reverse_i1") slopes = {-t, -t, t, -t};
    std::vector<std::array<Point, 2>> faces{{Point{-5, 0}, Point{-5, h}}};
    for (std::size_t k = 0; k < slopes.size(); ++k) {
        const Rational center(static_cast<std::int64_t>(-3 + 2 * static_cast<int>(k)));
        faces.push_back({Point{center - slopes[k] * h / q(2), 0}, Point{center + slopes[k] * h / q(2), h}});
    }
    faces.push_back({Point{5, 0}, Point{5, h}});
    Model m;
    std::vector<contact::Body2> bodies;
    for (std::size_t i = 0; i + 1 < faces.size(); ++i)
        bodies.push_back(body("b" + std::to_string(i), {faces[i][0], faces[i + 1][0], faces[i + 1][1], faces[i][1]}, i == 0 || i == 4, origin));
    m.assembly = assembly(std::move(bodies));
    m.loads.resize(5); m.loads[2].live = {0, -1, origin[0]};
    return m;
}
Model transform(const Model& input, Rational cosine, Rational sine, Rational scale, Point shift) {
    Model out = input;
    auto rotate = [&](Point p) -> Point { return {cosine * p[0] - sine * p[1], sine * p[0] + cosine * p[1]}; };
    auto location = [&](Point p) -> Point { auto r = rotate(p); return {scale * r[0] + shift[0], scale * r[1] + shift[1]}; };
    for (std::size_t i = 0; i < input.assembly.bodies.size(); ++i) {
        const auto& old = input.assembly.bodies[i];
        geom::Polygon ring;
        for (const auto& p : old.geometry.vertices) ring.push_back(location(p));
        out.assembly.bodies[i] = contact::Body2(old.body_id, geom::Body(ring), location(old.reference_point),
            old.boundary_type, old.dof_mask, location(old.dof_anchor));
        for (const bool live : {false, true}) {
            auto& target = live ? out.loads[i].live : out.loads[i].dead;
            const auto& source = live ? input.loads[i].live : input.loads[i].dead;
            const auto f = rotate({source[0], source[1]});
            target = {f[0], f[1], scale * source[2]};
        }
    }
    return out;
}
void rigid_units_and_anchor_translation() {
    const auto m = floor_model();
    for (const auto rotation : {Point{1, 0}, Point{0, 1}, Point{q(3, 5), q(4, 5)}, Point{q(-5, 13), q(12, 13)}})
        for (const Rational scale : {q(1, 1024), q(1), q(16)})
            for (const std::int64_t distance : {0, 1000, 100000}) {
                const auto moved = transform(m, rotation[0], rotation[1], scale, {distance, -q(3) * q(distance)});
                const auto r = limit_load_ideal_exact_2d(moved.assembly, moved.loads, q(1, 4));
                require(r.exact_value == q(1, 4), "rational rigid transform scale and tiny feature preserve nondimensional load factor");
                verify(r);
            }
    // Translating the plate and its physical anchor together must preserve the
    // same mask, while changing only the origin is a separate reparameterization.
    const auto original = beam(3, 1, 1, {1, 0, 1});
    const auto shifted = transform(original, q(1), q(0), q(1), {100000, -1000});
    const auto r = limit_load_ideal_exact_2d(shifted.assembly, shifted.loads, q(2));
    require(r.exact_value == q(4, 3), "physical plate anchor moves with translated geometry");
    verify(r);
}
void valid_implications_and_reverse_counterexample() {
    auto boxed = assembly({body("A", rectangle(0, 1)), body("L", rectangle(-1, 0), true),
        body("R", rectangle(1, 2), true), body("U", rectangle(0, 1, 1, 2), true), body("D", rectangle(0, 1, -1, 0), true)});
    auto seam = assembly({body("A", rectangle(0, 1)), body("L", rectangle(-1, 0), true), body("R", rectangle(1, 2), true)});
    auto plane = assembly({body("A", rectangle(0, 1)), body("D", rectangle(0, 1, -1, 0), true)});
    auto free = assembly({body("A", rectangle(0, 1))});
    for (const auto& a : {boxed, seam, plane, free}) {
        const auto cs = contact::assemble_contact_set2(a);
        const auto first = contact::first_order_mobility(cs);
        bool six_unbounded = true;
        for (std::size_t axis = 0; axis < 3; ++axis) for (const int sign : {-1, 1}) {
            Loads2 loads(a.bodies.size()); loads[0].live[axis] = q(sign);
            const auto r = limit_load_ideal_exact_2d(cs, loads, q(0));
            verify(r);
            six_unbounded = six_unbounded && r.mathematical_status == "UNBOUNDED";
        }
        require(six_unbounded == first.cone_is_zero.value(), "mu zero single-body immobility iff six load directions unbounded");
        if (first.cone_is_zero.value()) for (const Rational mu : {q(0), q(1, 4), q(2)}) {
            Loads2 loads(a.bodies.size()); loads[0].dead = {q(7, 8), q(-9, 4), q(11, 2)}; loads[0].live = {q(-5, 4), q(3, 8), q(-7, 2)};
            const auto r = limit_load_ideal_exact_2d(cs, loads, mu);
            require(r.mathematical_status == "UNBOUNDED", "single-body zero cone implies unbounded at varied mu and nonsymmetric loads");
            verify(r);
            // Independent conic reconstruction from L1's signed coordinate
            // certificates, not from the LP result: equal generator weights
            // cancel friction identically for every nonnegative mu.
            const auto& p = *r.problem;
            const auto& normals = *first.matrix;
            require(p.c.size() == 2 * normals.size() + 1, "one paired friction generator per retained normal");
            for (std::size_t j = 0; j < normals.size(); ++j)
                for (std::size_t k = 0; k < p.A.size(); ++k)
                    require(p.A[k][2 * j] + p.A[k][2 * j + 1] == q(2) * normals[j][k], "g minus plus g plus equals twice normal identically");
            auto conic_force = [&](const Vector& target) {
                Vector x(p.c.size());
                for (std::size_t k = 0; k < target.size(); ++k) {
                    if (target[k] == q(0)) continue;
                    const int sign = target[k] > q(0) ? 1 : -1;
                    const auto proof = std::find_if(first.zero_certificates->begin(), first.zero_certificates->end(),
                        [&](const auto& item) { return item.coordinate == k && item.sign == sign; });
                    require(proof != first.zero_certificates->end(), "signed coordinate normal combination present");
                    for (std::size_t j = 0; j < normals.size(); ++j) {
                        require(proof->multipliers[j] >= q(0), "signed basis coefficients nonnegative");
                        const auto weight = eab2::exact::abs(target[k]) * proof->multipliers[j] / q(2);
                        x[2 * j] = x[2 * j] + weight; x[2 * j + 1] = x[2 * j + 1] + weight;
                    }
                }
                return x;
            };
            const auto x0 = conic_force(p.b);
            Vector negative_live;
            for (const auto& row : p.A) negative_live.push_back(-row.back());
            auto ray = conic_force(negative_live); ray.back() = q(1);
            for (std::size_t k = 0; k < p.A.size(); ++k) {
                require(dot(p.A[k], x0) == p.b[k], "signed basis constructs feasible point for given dead wrench");
                require(dot(p.A[k], ray) == q(0), "signed basis constructs improving ray for given live wrench");
            }
        }
    }
    // G5 middle body is the explicit invalid converse: freezing its neighbours
    // permits unbounded clamping, while the actual moving chain has finite P.
    const auto chain = beam();
    auto single = chain.assembly;
    for (std::size_t i = 0; i < single.bodies.size(); ++i) if (i != 2) {
        single.bodies[i].boundary_type = "FIXED_BODY"; single.bodies[i].dof_mask = {0, 0, 0};
    }
    const auto multi = limit_load_ideal_exact_2d(chain.assembly, chain.loads, q(1, 4));
    const auto isolated = limit_load_ideal_exact_2d(single, chain.loads, q(1, 4));
    require(multi.exact_value == q(1, 2) && isolated.mathematical_status == "UNBOUNDED", "G5 middle body rejects single-to-multi converse");
    verify(multi); verify(isolated);
    require(contact::first_order_mobility(single).cone_is_zero == false, "single unbounded is not a first-order lock");
    // A genuine multi-body antecedent: fixed outer faces, independent live load
    // only on the central body; the same chain without a finite-pressure plate.
    auto locked_chain = chain.assembly;
    locked_chain.bodies.back().boundary_type = "FIXED_BODY"; locked_chain.bodies.back().dof_mask = {0, 0, 0};
    const auto together = limit_load_ideal_exact_2d(locked_chain, chain.loads, q(1, 4));
    require(together.mathematical_status == "UNBOUNDED" && isolated.mathematical_status == "UNBOUNDED", "multi unbounded with local live load implies single unbounded");
    verify(together);
    for (const std::string orientation : {"koureas", "unreversed", "reverse_i1"}) {
        const auto m = five_block_chain(orientation);
        const Rational mu = orientation == "koureas" ? q(0) : orientation == "unreversed" ? q(1, 2) : q(1, 4);
        const auto full = limit_load_ideal_exact_2d(m.assembly, m.loads, mu);
        auto local = m.assembly;
        for (std::size_t i = 0; i < local.bodies.size(); ++i) if (i != 2) {
            local.bodies[i].boundary_type = "FIXED_BODY"; local.bodies[i].dof_mask = {0, 0, 0};
        }
        const auto center = limit_load_ideal_exact_2d(local, m.loads, mu);
        require(full.mathematical_status == "UNBOUNDED" && center.mathematical_status == "UNBOUNDED", "G1 three orientations reproduce local-load valid implication");
        verify(full); verify(center);
    }
}
} // namespace
int main() {
    try {
        g5_closed_form_and_masks(); matrix_and_certificates(); rigid_units_and_anchor_translation();
        valid_implications_and_reverse_counterexample();
        std::cout << "C3L3_STATICS_OK checks=" << checks << '\n';
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "C3L3_STATICS_FAIL " << e.what() << '\n';
        return 1;
    }
}
