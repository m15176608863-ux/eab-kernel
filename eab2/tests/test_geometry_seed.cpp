#include "geometry_seed.hpp"
#include <algorithm>
#include <iostream>
#include <stdexcept>

using namespace eab2::statics;
namespace geom = eab2::geometry2;
namespace contact = eab2::contact;
namespace {
int checks = 0;
void require(bool value, const char* name) { ++checks; if (!value) throw std::runtime_error(name); }
Rational q(std::int64_t n, std::int64_t d = 1) { return Rational(eab2::exact::Int(n), eab2::exact::Int(d)); }
struct Model { LimitProblem2 problem; GeometrySeed2 seed; };
Model model(bool clockwise = false, bool edge_on_b = false) {
    geom::Polygon a{{0, 0}, {2, 0}, {2, 3}, {0, 3}}, b{{-2, 0}, {0, 0}, {0, 3}, {-2, 3}};
    if (clockwise) { std::reverse(a.begin(), a.end()); std::reverse(b.begin(), b.end()); }
    contact::ContactSet2 cs;
    cs.assembly.bodies.emplace_back("A", geom::Body(a), Point{q(5, 8), q(-3, 8)}, "", std::array<int, 3>{1, 1, 1}, Point{q(1, 4), q(7, 8)});
    cs.assembly.bodies.emplace_back("B", geom::Body(b), Point{0, 0}, "FIXED_BODY", std::array<int, 3>{0, 0, 0});
    cs.assembly.completeness = cs.completeness = "complete";
    cs.status = cs.mathematical_status = "RESOLVED";
    for (const Point point : {Point{0, 0}, Point{0, 3}}) {
        const std::array<std::size_t, 2> edge = clockwise ? std::array<std::size_t, 2>{0, 3} : std::array<std::size_t, 2>{3, 0};
        const std::array<std::size_t, 2> b_edge = clockwise ? std::array<std::size_t, 2>{2, 1} : std::array<std::size_t, 2>{1, 2};
        contact::ContactLabel2 label{"A", "B", point, edge_on_b ? "B" : "A", edge_on_b ? b_edge : edge};
        cs.constraints.push_back({0, 1, point, Point{0, -3}, {}, label});
    }
    Loads2 loads(2);
    loads[0].dead = {2, -3, 5}; loads[0].live = {-1, 4, -2};
    Model out;
    out.problem = build_limit_problem2(cs, loads, q(1, 4));
    out.seed.parameter = "shared_shape_load_anchor";
    out.seed.mu = q(7, 5);
    out.seed.bodies = {{"A", {7, 11, 13}, {17, -19, 23}, {-2, 3}}, {"B"}};
    for (const auto& body : cs.assembly.bodies) {
        const auto& raw = body.body_id == "A" ? a : b;
        for (std::size_t i = 0; i < raw.size(); ++i) {
            const auto& p = raw[i];
            out.seed.vertices.push_back({body.body_id, i, Point{q(2) * p[0] + q(3) * p[1] + q(5), -p[0] + q(4) * p[1] - q(2)}});
        }
    }
    return out;
}
void raw_geometry_and_load_anchor_oracle() {
    // Primary oracle: hand derivatives of a vertical edge and force-at-anchor
    // determinant. No production LP builder or seed helper computes expected.
    for (bool clockwise : {false, true}) for (bool edge_on_b : {false, true}) {
        const auto m = model(clockwise, edge_on_b);
        const auto d = propagate_geometry_seed2(m.problem, m.seed);
        require(d.parameter == "shared_shape_load_anchor", "parameter identity retained");
        require(d.dA.size() == 3 && d.dA[0].size() == 5, "original matrix shape");
        for (std::size_t j = 0; j < 4; ++j) {
            const auto s = q(j % 2 ? 1 : -1);
            require(d.dA[0][j] == q(12) - q(9, 4) * s, "point tangent normal and mu x propagation");
            require(d.dA[1][j] == -q(9) - q(36, 5) * s, "point tangent normal and mu y propagation");
        }
        require(d.dA[2][0] == q(111, 4) + q(867, 160), "force moment derivative at physical anchor minus");
        require(d.dA[2][1] == q(111, 4) - q(867, 160), "force moment derivative at physical anchor plus");
        require(d.dA[0].back() == q(17) && d.dA[1].back() == -q(19), "live seed is alpha matrix column");
        // anchor-reference=(-3/8,5/4), d_anchor=(-2,3).
        require(d.dA[2].back() == q(337, 8), "live seed includes moving anchor moment");
        require(d.db == Vector{-7, -11, -q(207, 8)}, "dead seed includes negative RHS and moving anchor moment");
        require(d.dc == Vector(5), "objective coefficient remains constant");
    }
}
void b_side_edge_tangent_original_vertex_seed() {
    // Edge B[1]->B[2]=(0,3), but the retained a-on-b force tangent is (0,-3).
    // Raw affine vertices have d(edge)=(9,12), so dT=(-9,-12).
    auto m = model(false, true); m.seed.mu = 0;
    const auto d = propagate_geometry_seed2(m.problem, m.seed);
    require(d.dA[0][0] == q(57, 4) && d.dA[1][0] == -q(6), "b_side_minus_generator_hand_derivative");
    require(d.dA[0][1] == q(39, 4) && d.dA[1][1] == -q(12), "b_side_plus_generator_hand_derivative");
    std::cout << "PASS b_side_edge_tangent_original_vertex_seed\n";
}
template<class Change> void invalid(Change change, const char* name) {
    auto m = model(); change(m.seed);
    bool caught = false;
    try { validate_geometry_seed2(m.problem.contact_set, m.seed); }
    catch (const std::invalid_argument&) { caught = true; }
    require(caught, name);
}
void identity_and_shared_interface_rejections() {
    invalid([](auto& s) { s.vertices.pop_back(); }, "missing vertex rejected");
    invalid([](auto& s) { std::swap(s.vertices[0], s.vertices[1]); }, "vertex order rejected");
    invalid([](auto& s) { s.vertices[0].vertex_id = 10; }, "wrong original vertex ID rejected");
    invalid([](auto& s) { std::swap(s.bodies[0], s.bodies[1]); }, "body order rejected");
    invalid([](auto& s) { s.bodies.pop_back(); }, "body count rejected");
    invalid([](auto& s) { s.vertices[5].derivative[0] = q(200); }, "contradictory shared vertex jet rejected");
}
void translated_anchor_and_reference_covariance() {
    // Simultaneous translation leaves every relative-arm derivative unchanged.
    // This checks original-ID propagation even at large coordinates.
    const auto base = model();
    const auto expected = propagate_geometry_seed2(base.problem, base.seed);
    for (const Point offset : {Point{0, 0}, Point{600, 800}, Point{60000, 80000}}) {
        auto p = base.problem;
        for (auto& b : p.contact_set.assembly.bodies) {
            for (auto& v : b.geometry.vertices) v = geom::add(v, offset);
            b.reference_point = geom::add(b.reference_point, offset);
            b.dof_anchor = geom::add(b.dof_anchor, offset);
        }
        for (auto& c : p.contact_set.constraints) { c.point = geom::add(c.point, offset); c.label.point = c.point; }
        const auto actual = propagate_geometry_seed2(p, base.seed);
        require(actual.dA == expected.dA && actual.db == expected.db && actual.dc == expected.dc,
            "shared geometry jet translation covariance about moved anchors");
    }
    // Frozen reference changes are a load-coordinate change, not support motion.
    auto shifted = base.problem;
    auto jet = base.seed;
    const Point offset{q(7, 3), q(-11, 5)};
    shifted.contact_set.assembly.bodies[0].reference_point = geom::add(shifted.contact_set.assembly.bodies[0].reference_point, offset);
    for (auto pair : {std::pair<Wrench*, Wrench*>{&shifted.loads[0].dead, &jet.bodies[0].dead},
                      std::pair<Wrench*, Wrench*>{&shifted.loads[0].live, &jet.bodies[0].live}}) {
        (*pair.first)[2] = (*pair.first)[2] - geom::cross(offset, Point{(*pair.first)[0], (*pair.first)[1]});
        (*pair.second)[2] = (*pair.second)[2] - geom::cross(offset, Point{(*pair.second)[0], (*pair.second)[1]});
    }
    const auto actual = propagate_geometry_seed2(shifted, jet);
    require(actual.dA == expected.dA && actual.db == expected.db, "frozen reference reparameterization preserves anchor jets");
}
} // namespace
int main() {
    try {
        raw_geometry_and_load_anchor_oracle();
        b_side_edge_tangent_original_vertex_seed();
        identity_and_shared_interface_rejections();
        translated_anchor_and_reference_covariance();
        std::cout << "C3L4_GEOMETRY_SEED_OK checks=" << checks << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "C3L4_GEOMETRY_SEED_FAIL " << error.what() << '\n'; return 1;
    }
}
