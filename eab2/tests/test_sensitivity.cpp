#include "sensitivity.hpp"
#include "geometry_seed.hpp"
#include "branch.hpp"
#include <map>
#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <tuple>

using namespace eab2::statics;
namespace ct = eab2::contact;
namespace geom = eab2::geometry2;
namespace {
int checks = 0;
void require(bool condition, const char* message) { ++checks; if (!condition) throw std::runtime_error(message); }
Rational q(std::int64_t n, std::int64_t d = 1) { return Rational(eab2::exact::Int(n), eab2::exact::Int(d)); }
LimitProblem2 problem(Matrix A, Vector b, Vector c) {
    LimitProblem2 p;
    p.A = std::move(A); p.b = std::move(b); p.c = std::move(c); p.column_labels.resize(p.c.size());
    return p;
}
SensitivityOptions2 parameter(const std::string& name) { SensitivityOptions2 o; o.parameter = name; return o; }
void slopes(const SensitivityResult2& r, Rational right, Rational left, const std::string& kind, const char* message) {
    require(r.call_status == "OK" && r.differentiability == kind && r.right_derivative == right && r.left_derivative == left, message);
    require(r.directional_derivative == right && r.display_status == "EXACT", "exact non-null directional payload");
}
void stable_original_unscaled_dual_three_seeds() {
    // Independent elementary oracle: (4+3p)(3+2p)/(2+p), derivative 11/2.
    // Uses neither production inversion nor a geometric force construction.
    auto r = solve_limit_problem2(problem({{2, 1}}, {3}, {4, 0}));
    const LimitSeed2 seed{{{1, 0}}, {2}, {3, 0}, "p"};
    auto d = evaluate_sensitivity2(r, seed, parameter("p"));
    slopes(d, q(11, 2), q(11, 2), "smooth", "stable original unscaled y and dA/db/dc formula");
    require(d.method == "stable_basis", "nondegenerate example selects stable formula");
    require(d.piece_jacobians.size() == 1 && d.piece_jacobians[0].derivative == q(11, 2), "stable basis Jacobian retained");
    r.exact_y = Vector{1};
    bool rejected = false;
    try { (void)evaluate_sensitivity2(r, seed, parameter("p")); } catch (const std::logic_error&) { rejected = true; }
    require(rejected, "scaled or counterfeit y is not an original-model certificate");
}
void min_max_mapping_and_reverse_direction() {
    // Oracle is min p*x1 on the scalar interval 0<=x1<=1, not another LP.
    const auto r = solve_limit_problem2(problem({{1, 1}}, {1}, {0, 0}));
    const LimitSeed2 seed{{{0, 0}}, {0}, {-1, 0}, "p"}; // c_max = -c_min.
    auto options = parameter("p"); options.tied_labels = {std::string("x1"), std::string("x2")};
    const auto d = evaluate_sensitivity2(r, seed, options);
    slopes(d, 0, -1, "one_sided", "min mapping must give min right slope zero, not one");
    require(-*d.right_derivative == 0 && -*d.left_derivative == 1, "max slopes map back to min slopes");
    require(d.method == "mills_freund" && d.forward_certificate && d.reverse_certificate, "bounded face uses two certified directional LPs");
    require(d.tied_labels.size() == 2, "nonunique labels preserved");
    const auto json = export_exact(d);
    require(json.find("\"tied_labels\":[\"x1\",\"x2\"]") != std::string::npos, "caller string labels keep JSON string type");
}
void both_optimal_recession_guards() {
    const auto primal = solve_limit_problem2(problem({{1, 0}}, {1}, {0, 0}));
    const auto p = evaluate_sensitivity2(primal, LimitSeed2{{{0, 0}}, {0}, {0, 1}}, parameter("p"));
    require(p.differentiability == "singular" && p.reason == "possibly_discontinuous", "primal optimal recession reports conservative singularity");
    require(p.primal_recession_ray == Vector({0, 1}) && !p.right_derivative && !p.left_derivative, "primal recession witness and no slope");
    const auto dual = solve_limit_problem2(problem({{1}, {0}}, {1, 0}, {1}));
    const auto d = evaluate_sensitivity2(dual, LimitSeed2{{{0}, {0}}, {0, 0}, {1}}, parameter("p"));
    require(d.differentiability == "singular" && d.dual_recession_ray && !d.directional_derivative, "dual null-space recession has no fabricated slope");
    require((*d.dual_recession_ray)[0] == 0 && (*d.dual_recession_ray)[1] != 0, "dual recession independently annihilates A and b");
}
struct Beam { ct::ContactSet2 contacts; Loads2 loads; Rational height, pressure; };
Beam g5(Rational h = 1, Rational pressure = 1, Point origin = {q(5, 8), q(-3, 8)}) {
    // Primary oracle has handwritten vertical endpoint force cones; it does
    // not call the production contact assembler or its source-label helpers.
    Beam beam; beam.height = h; beam.pressure = pressure;
    auto& cs = beam.contacts;
    cs.status = "RESOLVED"; cs.mathematical_status = "RESOLVED"; cs.completeness = "complete";
    cs.assembly.completeness = "complete"; beam.loads.resize(5);
    for (int i = 0; i < 5; ++i) {
        const auto x = q(i - 1);
        const bool fixed = i == 0, plate = i == 4;
        cs.assembly.bodies.emplace_back("b" + std::to_string(i), geom::Body({{x, 0}, {x + q(1), 0}, {x + q(1), h}, {x, h}}),
            origin, fixed ? "FIXED_BODY" : (plate ? "FORCE_CONTROLLED_PLATE" : ""),
            fixed ? std::array<int, 3>{0, 0, 0} : (plate ? std::array<int, 3>{1, 0, 0} : std::array<int, 3>{1, 1, 1}), origin);
    }
    beam.loads[2].live = {0, -1, -(q(3, 2) - origin[0])};
    beam.loads[4].dead = {-pressure, 0, (h / q(2) - origin[1]) * pressure};
    for (std::size_t i = 0; i < 4; ++i) for (const auto& y : Vector{0, h}) {
        const Point point{q(static_cast<std::int64_t>(i)), y};
        const ct::ContactLabel2 label{cs.assembly.bodies[i + 1].body_id, cs.assembly.bodies[i].body_id,
            point, cs.assembly.bodies[i + 1].body_id, {0, 3}};
        cs.constraints.push_back({i + 1, i, point, {0, -h}, {}, label});
    }
    return beam;
}
LimitSeed2 contact_seed(const LimitProblem2& p, const std::vector<std::pair<Point, Point>>& derivatives,
                       Rational dmu = 0, const Loads2& load_derivatives = {}) {
    LimitSeed2 seed{Matrix(p.A.size(), Vector(p.c.size())), Vector(p.b.size()), Vector(p.c.size()), "p"};
    const auto& bodies = p.contact_set.assembly.bodies;
    std::size_t column = 0;
    for (std::size_t k = 0; k < p.contact_set.constraints.size(); ++k) {
        const auto& c = p.contact_set.constraints[k];
        const auto [dp, dt] = derivatives[k];
        for (int sign : {-1, 1}) {
            const Point f{-c.tangent[1] + q(sign) * p.mu * c.tangent[0], c.tangent[0] + q(sign) * p.mu * c.tangent[1]};
            const Point df{-dt[1] + q(sign) * (dmu * c.tangent[0] + p.mu * dt[0]), dt[0] + q(sign) * (dmu * c.tangent[1] + p.mu * dt[1])};
            std::size_t row = 0;
            for (std::size_t i = 0; i < bodies.size(); ++i) {
                const auto& b = bodies[i]; if (b.boundary_type == "FIXED_BODY") continue;
                const auto sense = q(static_cast<int>(i == c.a) - static_cast<int>(i == c.b));
                const Point arm{c.point[0] - b.dof_anchor[0], c.point[1] - b.dof_anchor[1]};
                const Wrench dw{sense * df[0], sense * df[1], sense * (dp[0] * f[1] - dp[1] * f[0] + arm[0] * df[1] - arm[1] * df[0])};
                for (std::size_t j = 0; j < 3; ++j) if (b.dof_mask[j]) seed.dA[row++][column] = dw[j];
            }
            ++column;
        }
    }
    if (!load_derivatives.empty()) {
        std::size_t row = 0;
        for (std::size_t i = 0; i < bodies.size(); ++i) {
            const auto& b = bodies[i]; if (b.boundary_type == "FIXED_BODY") continue;
            const auto offset = geom::sub(b.dof_anchor, b.reference_point);
            auto live = load_derivatives[i].live, dead = load_derivatives[i].dead;
            live[2] = live[2] - geom::cross(offset, {live[0], live[1]});
            dead[2] = dead[2] - geom::cross(offset, {dead[0], dead[1]});
            for (std::size_t j = 0; j < 3; ++j) if (b.dof_mask[j]) { seed.dA[row][column] = live[j]; seed.db[row++] = -dead[j]; }
        }
    }
    return seed;
}
LimitSeed2 beam_seed(const LimitProblem2& p, const Beam& b, const std::string& name) {
    std::vector<std::pair<Point, Point>> jets(p.contact_set.constraints.size());
    Loads2 loads(b.loads.size());
    if (name == "h") {
        for (std::size_t k = 0; k < jets.size(); ++k) {
            const auto& c = p.contact_set.constraints[k];
            jets[k] = {{0, c.point[1] / b.height}, {0, c.tangent[1] / b.height}};
        }
        loads.back().dead[2] = b.pressure / q(2);
    } else if (name == "P") {
        for (std::size_t k = 0; k < 3; ++k) loads.back().dead[k] = b.loads.back().dead[k] / b.pressure;
    } else if (name == "load_scale") loads[2].live = b.loads[2].live;
    auto seed = contact_seed(p, jets, name == "mu" ? q(1) : q(0), loads); seed.parameter = name; return seed;
}
void g5_mills_smooth_and_switch() {
    // Hand oracle: F=min(2*mu*P, 2*P*h) for n=L=3, b=1.
    for (const auto mu : Vector{q(1, 4), 2}) {
        const auto beam = g5(); const auto r = limit_load_ideal_exact_2d(beam.contacts, beam.loads, mu);
        for (const std::string name : {"mu", "P", "h"}) {
            const auto d = evaluate_sensitivity2(r, beam_seed(*r.problem, beam, name), parameter(name));
            const auto expected = name == "mu" ? (mu < q(1) ? q(2) : q(0)) :
                (name == "P" ? (mu < q(1) ? q(1, 2) : q(2)) : (mu < q(1) ? q(0) : q(2)));
            slopes(d, expected, expected, "smooth", "G5 bounded-face exact closed-form derivative");
            require(d.method == "mills_freund", "degenerate G5 does not use arbitrary stable-basis formula");
        }
    }
    const auto beam = g5(); const auto r = limit_load_ideal_exact_2d(beam.contacts, beam.loads, 1);
    for (const std::string name : {"mu", "h", "P"}) {
        const auto d = evaluate_sensitivity2(r, beam_seed(*r.problem, beam, name), parameter(name));
        slopes(d, name == "P" ? q(2) : q(0), 2, name == "P" ? "smooth" : "one_sided", "G5 switch preserves right zero and left two");
    }
    const auto zero = evaluate_sensitivity2(limit_load_ideal_exact_2d(beam.contacts, beam.loads, 0));
    require(zero.differentiability == "singular" && zero.reason == "possibly_discontinuous" && zero.dual_recession_ray,
        "mu zero dual recession rejects a tempting closed-form right slope");
    require(!zero.left_derivative && !zero.right_derivative, "mu zero has no slope");
}
void live_load_column_is_not_rhs() {
    const auto beam = g5(); const auto r = limit_load_ideal_exact_2d(beam.contacts, beam.loads, q(1, 4));
    const auto seed = beam_seed(*r.problem, beam, "load_scale");
    const auto d = evaluate_sensitivity2(r, seed, parameter("load_scale"));
    slopes(d, q(-1, 2), q(-1, 2), "smooth", "live amplitude derivative is negative capacity");
    require(std::all_of(seed.db.begin(), seed.db.end(), [](const auto& v) { return v == q(0); }) &&
        std::any_of(seed.dA.begin(), seed.dA.end(), [](const auto& row) { return row.back() != q(0); }), "live jet occupies A not b");
}
void unstable_basis_cannot_hide_switch() {
    // Defect killer checks the independent one-sided derivative values before
    // any method metadata: choosing an arbitrary basis cannot produce both.
    const auto beam = g5();
    const auto result = limit_load_ideal_exact_2d(beam.contacts, beam.loads, 1);
    const auto derivative = evaluate_sensitivity2(result, beam_seed(*result.problem, beam, "mu"));
    require(derivative.right_derivative == q(0) && derivative.left_derivative == q(2),
        "unstable fixed basis loses G5 switch right zero / left two");
    require(derivative.differentiability == "one_sided", "G5 switch is not smooth");
}
void validity_direction_and_dimension_contracts() {
    auto r = solve_limit_problem2(problem({{2, 1}}, {3}, {4, 0}));
    r.validity_conditions = {"true_vv_excluded_from_statics"};
    const LimitSeed2 seed{{{1, 0}}, {2}, {3, 0}, "p"};
    auto options = parameter("p"); options.validity_conditions = {"L1接触骨架不变", "shared_parameter"}; options.positive_direction_valid = false;
    const auto one = evaluate_sensitivity2(r, seed, options);
    require(one.differentiability == "one_sided" && !one.right_derivative && one.left_derivative == q(11, 2), "negative-only valid direction");
    require(one.validity_conditions == std::vector<std::string>({"L1接触骨架不变", "shared_parameter", "true_vv_excluded_from_statics"}), "required validity conditions retained and deduplicated");
    options.negative_direction_valid = false;
    require(evaluate_sensitivity2(r, seed, options).reason == "no_valid_direction", "no direction is not a slope");
    require(evaluate_sensitivity2(r, LimitSeed2{}, parameter("p")).call_status == "INVALID_INPUT", "seed shape mismatch rejected");
    require(evaluate_sensitivity2(r, std::nullopt, parameter("p")).call_status == "UNSUPPORTED", "nonmu direction requires exact seed");
    const auto unbounded = solve_limit_problem2(problem({{1, -1}}, {0}, {0, 1}));
    const auto d = evaluate_sensitivity2(unbounded);
    require(d.reason == "finite_optimum_required" && !d.directional_derivative && d.quality == "exact_jet", "frozen null-slope quality never means a certified derivative");
}
struct Model { ct::Assembly2 assembly; Loads2 loads; };
Model g1(Rational t, Rational h, const std::string& orientation) {
    const auto signs = orientation == "unreversed" ? std::vector<int>{1, -1, 1, -1} :
        (orientation == "reverse_i1" ? std::vector<int>{-1, -1, 1, -1} : std::vector<int>{-1, -1, 1, 1});
    std::vector<std::array<Point, 2>> faces{{Point{-5, 0}, Point{-5, h}}};
    for (std::size_t k = 0; k < 4; ++k) {
        const auto x = q(-3 + 2 * static_cast<int>(k)), slope = q(signs[k]) * t;
        faces.push_back({Point{x - slope * h / q(2), 0}, Point{x + slope * h / q(2), h}});
    }
    faces.push_back({Point{5, 0}, Point{5, h}});
    Model model; model.assembly.completeness = "complete"; model.assembly.pairs.emplace(); model.loads.resize(5);
    for (std::size_t i = 0; i < 5; ++i) for (std::size_t j = i + 1; j < 5; ++j)
        model.assembly.pairs->push_back({i, j});
    const Point origin{q(5, 8), q(-3, 8)};
    for (std::size_t i = 0; i < 5; ++i) {
        const bool fixed = i == 0 || i == 4;
        model.assembly.bodies.emplace_back("block_" + std::to_string(i + 1),
            geom::Body({faces[i][0], faces[i + 1][0], faces[i + 1][1], faces[i][1]}), origin,
            fixed ? "FIXED_BODY" : "", fixed ? std::array<int, 3>{0, 0, 0} : std::array<int, 3>{1, 1, 1}, origin);
    }
    model.loads[2].live = {0, -1, origin[0]}; return model;
}
LimitSeed2 g1_seed(const LimitProblem2& p, Rational t, Rational h, const std::string& name, int face = 0) {
    std::vector<std::pair<Point, Point>> jets;
    std::map<Point, Point> velocities;
    for (const auto& c : p.contact_set.constraints) {
        const auto slope = c.tangent[0] / c.tangent[1];
        Point velocity = name == "t" ? Point{slope / t * (c.point[1] - h / q(2)), 0} :
            Point{slope * (c.point[1] / h - q(1, 2)), c.point[1] / h};
        if (face && c.point[0] - slope * (c.point[1] - h / q(2)) != q(-5 + 2 * face)) velocity = {0, 0};
        velocities[c.point] = velocity;
    }
    GeometrySeed2 raw; raw.parameter = name;
    std::map<std::pair<std::string, std::size_t>, Point> ordered;
    for (const auto& body : p.contact_set.assembly.bodies) {
        raw.bodies.push_back({body.body_id});
        for (std::size_t k = 0; k < body.geometry.vertices.size(); ++k) {
            const auto& point = body.geometry.vertices[k];
            ordered[{body.body_id, body.geometry.original_vertex_ids[k]}] = velocities.contains(point) ? velocities.at(point) :
                (name == "h" ? Point{0, point[1] / h} : Point{0, 0});
        }
    }
    std::sort(raw.bodies.begin(), raw.bodies.end(), [](const auto& a, const auto& b) { return a.body_id < b.body_id; });
    for (const auto& [id, v] : ordered) raw.vertices.push_back({id.first, id.second, v});
    return propagate_geometry_seed2(p, raw);
}
void boundary_repeated_root_candidate_regression() {
    // Original shared-vertex affine data from the deterministic asymmetric
    // zero-threshold fixture. The reverse acquired basis has leading slack
    // v^2*(v-7/128); a non-square-free Sturm split at zero loses its positive
    // root. Expected slopes are independently checked by the L4 K oracle.
    const auto model = g1(0, 1, "koureas");
    const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
    require(critical.exact_threshold == 0, "repeated-root regression starts at original lower domain boundary");
    const std::array<std::array<int, 2>, 20> velocity{{
        {1, 3}, {2, 0}, {-2, -2}, {-2, -3},
        {2, 0}, {-1, -1}, {-2, -3}, {-2, -2},
        {-1, -1}, {-1, -1}, {-1, -3}, {-2, -3},
        {-1, -1}, {-1, -2}, {2, -3}, {-1, -3},
        {-1, -2}, {-2, 2}, {0, -1}, {2, -3}}};
    GeometrySeed2 raw; raw.parameter = "asym_random_rational_0";
    for (std::size_t i = 0; i < model.assembly.bodies.size(); ++i) {
        const auto& body = model.assembly.bodies[i]; raw.bodies.push_back({body.body_id});
        for (std::size_t k = 0; k < 4; ++k) raw.vertices.push_back({body.body_id, k,
            {q(velocity[4 * i + k][0], 64), q(velocity[4 * i + k][1], 64)}});
    }
    const auto d = evaluate_sensitivity2(critical,
        propagate_geometry_seed2(*critical.threshold_certificate->problem, raw), std::nullopt, parameter(raw.parameter));
    slopes(d, q(3, 128), q(-7, 128), "one_sided", "square-free candidates retain inward reverse branch past a repeated zero root");
    require(d.quality == "exact_jet" && d.method == "branch_certificate" && !d.tied_labels.empty(),
        "repeated-root candidate is accepted only with complete K certificates and root labels");
}
void open_and_closed_threshold_implicit_derivatives() {
    // Independent symbolic G1 oracles: mu=t, and mu=t-h*(1+t*t)/l (l=2).
    for (const auto& [orientation, h, name, expected, kind] :
        std::vector<std::tuple<std::string, Rational, std::string, Rational, std::string>>{
            {"unreversed", 1, "t", 1, "mechanism"}, {"unreversed", 1, "h", 0, "mechanism"},
            {"koureas", q(1, 4), "t", q(15, 16), "improving_ray"},
            {"koureas", q(1, 4), "h", q(-17, 32), "improving_ray"},
            {"reverse_i1", 1, "t", 1, "improving_ray"}}) {
        const auto model = g1(q(1, 4), h, orientation);
        const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
        require(critical.threshold_certificate && critical.threshold_certificate->problem, "G1 exact endpoint available");
        const auto d = evaluate_sensitivity2(critical, g1_seed(*critical.threshold_certificate->problem, q(1, 4), h, name), std::nullopt, parameter(name));
        slopes(d, expected, expected, "smooth", "G1 still-valid endpoint implicit derivative");
        require(d.method == "branch_certificate" && d.branch_certificate != "null", "open and closed full K certificate");
        require(!d.implicit_components.empty() && !d.tied_labels.empty(), "crossing components and ties retained");
        for (const auto& c : d.implicit_components) require(c.slope == expected && c.slope == -c.partial_parameter / c.partial_mu,
            "every implicit component exact quotient");
    }
}
void branch_faces_and_independent_beams_sweep(bool full) {
    // Independent closed forms: unreversed threshold is the maximum of the
    // simultaneously critical face branches; an isolated face contributes 1/2.
    // The default CTest run keeps one shared-direction case and one open
    // two-beam pair (about three minutes); the complete sweep (two
    // thicknesses, every face, open and closed pairs, three weightings,
    // about twenty minutes) runs with `--branch-sweep` and is also covered
    // query by query by the L4 `branch` differential family.
    for (const auto t : full ? Vector{q(1, 4), q(1, 8)} : Vector{q(1, 8)}) {
        const auto model = g1(t, 1, "unreversed");
        const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
        for (int face = 0; face <= (full ? 4 : 0); ++face) {
            std::cout << "BRANCH_PROGRESS single t=" << t.canonical() << " face=" << face << std::endl;
            const auto d = evaluate_sensitivity2(critical, g1_seed(*critical.threshold_certificate->problem, t, 1, "t", face), std::nullopt, parameter("t"));
            slopes(d, face ? q(1, 2) : q(1), face ? q(0) : q(1), face ? "one_sided" : "smooth", "all single faces and shared direction branch envelope");
            require(d.branch_certificate.find("\"status\":\"certified\"") != std::string::npos, "face value carries full K evidence");
        }
    }
    for (const bool closed : {false, true}) {
        if (!full && closed) continue;
        const Rational t = q(1, 4), h = closed ? q(1, 4) : q(1);
        Model combined;
        combined.assembly.completeness = "complete"; combined.assembly.pairs.emplace();
        for (int copy = 0; copy < 2; ++copy) {
            auto part = g1(t, h, closed ? "koureas" : "unreversed");
            const auto offset = combined.assembly.bodies.size();
            for (auto body : part.assembly.bodies) {
                body.body_id = std::string(copy ? "Q_" : "P_") + body.body_id;
                for (auto& v : body.geometry.vertices) v[0] = v[0] + q(20 * copy);
                body.reference_point[0] = body.reference_point[0] + q(20 * copy);
                body.dof_anchor[0] = body.dof_anchor[0] + q(20 * copy);
                combined.assembly.bodies.push_back(body);
            }
            for (const auto pair : *part.assembly.pairs) combined.assembly.pairs->push_back({pair[0] + offset, pair[1] + offset});
            combined.loads.insert(combined.loads.end(), part.loads.begin(), part.loads.end());
        }
        combined.assembly.pairs->clear();
        for (std::size_t i = 0; i < combined.assembly.bodies.size(); ++i)
            for (std::size_t j = i + 1; j < combined.assembly.bodies.size(); ++j) combined.assembly.pairs->push_back({i, j});
        const auto critical = critical_parameter(ct::assemble_contact_set2(combined.assembly), combined.loads, 1, 20);
        require(critical.attained == closed, "independent beams retain open or closed threshold");
        const auto& p = *critical.threshold_certificate->problem;
        for (const auto weights : full ? std::vector<std::pair<int, int>>{{1, 0}, {0, 1}, {1, 2}} : std::vector<std::pair<int, int>>{{1, 2}}) {
            std::cout << "BRANCH_PROGRESS pair closed=" << closed << " weights=" << weights.first << ',' << weights.second << std::endl;
            auto raw = *g1_seed(p, t, h, "t").geometry_path;
            for (auto& v : raw.vertices) for (auto& coordinate : v.derivative) coordinate = coordinate * q(v.body_id[0] == 'P' ? weights.first : weights.second);
            const auto d = evaluate_sensitivity2(critical, propagate_geometry_seed2(p, raw), std::nullopt, parameter("t"));
            const auto scale = closed ? q(15, 16) : q(1);
            slopes(d, scale * q(std::max(weights.first, weights.second)), scale * q(std::min(weights.first, weights.second)), "one_sided", "two independent beam branches require both envelope sides");
        }
    }
}
void branch_faces_and_independent_beams() { branch_faces_and_independent_beams_sweep(false); }
void branch_face2_regression() {
    const auto model = g1(q(1, 4), 1, "unreversed");
    const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
    const auto seed = g1_seed(*critical.threshold_certificate->problem, q(1, 4), 1, "t", 2);
    const auto d = evaluate_sensitivity2(critical, seed, std::nullopt, parameter("t"));
    slopes(d, q(1, 2), 0, "one_sided", "face2 branch right one-half left zero requires both K sides");
    require(d.branch_certificate.find("\"lower\":null") == std::string::npos &&
            d.branch_certificate.find("\"upper\":null") == std::string::npos,
        "certified directions carry lower, point and ray witnesses");
    require(!d.tied_labels.empty() && d.branch_certificate.find("\"singular\":true") != std::string::npos &&
        d.branch_certificate.find("\"leading_polynomial\":[") != std::string::npos,
        "singular acquired candidate keeps all leading-root labels and coefficients");
}
void branch_infeasible_lower_dual_with_load_jet() {
    const auto model = g1(q(1, 4), 1, "unreversed");
    const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
    const auto& p = *critical.threshold_certificate->problem;
    auto raw = *g1_seed(p, q(1, 4), 1, "t", 2).geometry_path;
    for (auto& body : raw.bodies) if (body.body_id == "block_3") {
        for (std::size_t k = 0; k < 3; ++k) { body.dead[k] = model.loads[2].live[k] / q(8); body.live[k] = model.loads[2].live[k] / q(16); }
    }
    // Positive load scaling and a signed dead offset change feasibility below
    // the open threshold but not its geometric branch envelope.
    const auto d = evaluate_sensitivity2(critical, propagate_geometry_seed2(p, raw), std::nullopt, parameter("load_shape"));
    slopes(d, q(1, 2), 0, "one_sided", "infeasible lower primal still admits the required dual branch certificate");
    // Deterministic asymmetric vertices plus both load jets. The reverse
    // envelope needs leading roots of an acquired correct-side singular basis.
    const std::array<std::array<int, 2>, 20> coordinates{{
        {3,3},{1,-3},{3,2},{-2,2}, {1,-3},{-2,-3},{2,-1},{3,2},
        {-2,-3},{-1,-2},{2,-1},{2,-1}, {-1,-2},{2,2},{0,1},{2,-1},
        {2,2},{-3,-3},{-3,-1},{0,1}}};
    require(raw.vertices.size() == coordinates.size(), "asymmetric original vertex inventory");
    for (std::size_t i = 0; i < coordinates.size(); ++i)
        raw.vertices[i].derivative = {q(coordinates[i][0], 64), q(coordinates[i][1], 64)};
    const auto general = evaluate_sensitivity2(critical, propagate_geometry_seed2(p, raw), std::nullopt, parameter("load_shape"));
    slopes(general, q(5, 128), q(-15, 512), "one_sided", "correct-side singular candidate and infeasible primal cannot lose reverse proof");
}
void branch_pure_load_jet_corpus_regression() {
    // Acceptance 2026-10-23: the corpus asymmetric dead_live channel (zero
    // vertex velocities, dead = live/8 and live = live/16 on the loaded block)
    // left the forward direction unresolved in C++ while the referee certified
    // smooth 0/0. The lower probe primal is INFEASIBLE there; the dual witness
    // must come from the homogeneous LP so that a basic point can be lifted.
    for (const auto t : Vector{q(1, 32), q(1, 4)}) {
        const auto model = g1(t, 1, "unreversed");
        const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
        const auto& p = *critical.threshold_certificate->problem;
        auto raw = *g1_seed(p, t, 1, "t").geometry_path;
        for (auto& v : raw.vertices) v.derivative = {0, 0};
        for (auto& body : raw.bodies) if (body.body_id == "block_3") {
            for (std::size_t k = 0; k < 3; ++k) { body.dead[k] = model.loads[2].live[k] / q(8); body.live[k] = model.loads[2].live[k] / q(16); }
        }
        std::cout << "BRANCH_PROGRESS pure load jet t=" << t.canonical() << std::endl;
        const auto d = evaluate_sensitivity2(critical, propagate_geometry_seed2(p, raw), std::nullopt, parameter("load_shape"));
        slopes(d, 0, 0, "smooth", "pure dead/live load jet keeps the open threshold: both directions certified zero");
        require(d.branch_certificate.find("\"status\":\"certified\"") != std::string::npos &&
                d.branch_certificate.find("\"status\":\"unresolved\"") == std::string::npos,
                "pure load jet carries full K evidence on both sides");
    }
}
void certified_shape_invariant_neutralises_witnessless_slope() {
    // Acceptance 2026-10-24: a slope without the three ordered-field witnesses
    // must never be emitted, and this invariant needs its own named gate.
    // The test seam makes certify() report such a slope; certified_threshold()
    // must turn it into unresolved with reason internal_certificate_shape.
    const auto model = g1(q(1, 4), 1, "unreversed");
    const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
    auto options = parameter("t"); options.test_witnessless_slope = true;
    const auto d = evaluate_sensitivity2(critical, g1_seed(*critical.threshold_certificate->problem, q(1, 4), 1, "t", 2), std::nullopt, options);
    require(d.differentiability == "unresolved" && !d.right_derivative && !d.left_derivative && !d.directional_derivative &&
            d.quality == "approximate" && d.reason == "internal_certificate_shape" && d.display_status == "NOT_APPLICABLE",
        "witnessless slope is neutralised by the certified-shape invariant");
    require(d.branch_certificate.find("\"status\":\"certified\"") == std::string::npos &&
            d.branch_certificate.find("\"status\":\"unresolved\"") != std::string::npos,
        "neutralised directions are exported as unresolved");
    const auto control = evaluate_sensitivity2(critical, g1_seed(*critical.threshold_certificate->problem, q(1, 4), 1, "t", 2), std::nullopt, parameter("t"));
    slopes(control, q(1, 2), 0, "one_sided", "the seam does not disturb the genuine face-2 certificate");
}
void ordered_field_and_raw_path_guards() {
    using P = branch_detail::Polynomial;
    P p; p.terms[{0, 1}] = 1; p.terms[{1, 0}] = -1;
    require(p.sign() == 1, "K epsilon before eta, not reversed");
    p.terms.clear(); p.terms[{7, 3}] = -1;
    require(p.sign() == -1, "nonzero high-order exact coefficient cannot be truncated to zero");
    const auto model = g1(q(1, 4), 1, "unreversed");
    const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
    auto seed = g1_seed(*critical.threshold_certificate->problem, q(1, 4), 1, "t");
    auto counterfeit = seed; counterfeit.dA[0][0] = counterfeit.dA[0][0] + q(1);
    const auto mismatch = evaluate_sensitivity2(critical, counterfeit, std::nullopt, parameter("t"));
    require(mismatch.reason == "affine_seed_mismatch" && mismatch.call_status == "INVALID_INPUT" &&
        mismatch.quality == "approximate" && mismatch.method == "branch_certificate",
        "raw primitives and matrix jet must bind to the same exact path");
    seed.geometry_path.reset();
    const auto missing = evaluate_sensitivity2(critical, seed, std::nullopt, parameter("t"));
    require(missing.differentiability == "unresolved" && !missing.right_derivative && missing.quality == "approximate", "matrix jet alone cannot certify full geometric path");
    for (int error = 0; error < 4; ++error) {
        auto unbound = critical;
        if (error == 0) unbound.original_mu_max.reset();
        if (error == 1) { unbound.original_mu_max = q(3, 5); unbound.original_mu_max_bits.reset(); }
        if (error == 2) unbound.original_mu_min = q(1);
        if (error == 3) unbound.original_mu_max_bits = UINT64_C(0x4000000000000000);
        const auto invalid = evaluate_sensitivity2(unbound, g1_seed(*critical.threshold_certificate->problem, q(1, 4), 1, "t"), std::nullopt, parameter("t"));
        require(invalid.differentiability == "unresolved" && !invalid.right_derivative && !invalid.left_derivative && invalid.quality == "approximate", "missing or inconsistent original domain never yields a K-certified value");
    }
}
void postfailure_candidate_singular_diagnostic() {
    // Real affine geometry and exact threshold. Candidate diagnosis is injected
    // here solely to test postfailure policy; this does NOT claim the smooth
    // geometry has a mathematical singularity. A zero pivot budget makes both
    // K attempts unavailable without changing the path or adding fake slopes.
    const auto model = g1(q(1, 4), 1, "unreversed");
    const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 20);
    const auto seed = g1_seed(*critical.threshold_certificate->problem, q(1, 4), 1, "t");
    auto limited = parameter("t"); limited.lp_options.max_pivots = 0;
    for (const auto* reason : {"critical_basis_singular", "zero_implicit_denominator"}) {
        SensitivityResult2 diagnostic; diagnostic.differentiability = "singular"; diagnostic.reason = reason;
        diagnostic.tied_labels.push_back(std::string("candidate_only_label"));
        const auto stopped = branch_detail::certified_threshold(critical, seed, limited, diagnostic);
        require(stopped.differentiability == "singular" && stopped.reason == reason && stopped.quality == "approximate" &&
            !stopped.right_derivative && !stopped.left_derivative && stopped.tied_labels.empty(), "postfailure preserves candidate singularity diagnosis without exact jet or candidate labels");
        const auto proved = branch_detail::certified_threshold(critical, seed, parameter("t"), diagnostic);
        slopes(proved, 1, 1, "smooth", "K certification overrides singular candidate diagnosis");
        auto missing_path = seed; missing_path.geometry_path.reset();
        require(branch_detail::certified_threshold(critical, missing_path, limited, diagnostic).differentiability == "unresolved", "missing path is not a singularity diagnosis");
        auto invalid_direction = limited; invalid_direction.negative_direction_valid = false;
        require(branch_detail::certified_threshold(critical, seed, invalid_direction, diagnostic).differentiability == "unresolved", "invalid direction is not a singularity diagnosis");
    }
}
void original_search_domain_boundary_certificate() {
    ct::Assembly2 assembly; assembly.completeness = "complete"; assembly.pairs = std::vector<std::array<std::size_t, 2>>{{0, 1}};
    assembly.bodies.emplace_back("fixed", geom::Body({{2, 2}, {3, 2}, {3, 3}, {2, 3}}), Point{q(3, 8), q(-5, 8)}, "FIXED_BODY", std::array<int, 3>{0, 0, 0});
    assembly.bodies.emplace_back("moving", geom::Body({{2, 3}, {3, 3}, {3, 4}, {2, 4}}), Point{q(3, 8), q(-5, 8)}, "", std::array<int, 3>{1, 1, 0}, Point{q(7, 16), q(9, 16)});
    Loads2 loads(2); loads[1].live = {1, -1, 0};
    const auto cs = ct::assemble_contact_set2(assembly);
    const auto critical = critical_parameter(cs, loads, 1, 20);
    require(critical.exact_threshold == 1 && critical.attained == true && critical.original_mu_max == 1, "raw search domain is retained separately from narrowed bracket");
    GeometrySeed2 raw; raw.parameter = "live_t";
    raw.bodies = {{"fixed"}, {"moving", {0, 0, 0}, {0, 1, 0}}};
    std::map<std::pair<std::string, std::size_t>, Point> ordered;
    for (const auto& body : assembly.bodies) for (std::size_t k = 0; k < body.geometry.vertices.size(); ++k)
        ordered[{body.body_id, body.geometry.original_vertex_ids[k]}] = {0, 0};
    for (const auto& [id, velocity] : ordered) raw.vertices.push_back({id.first, id.second, velocity});
    const auto d = evaluate_sensitivity2(critical, propagate_geometry_seed2(*critical.threshold_certificate->problem, raw), std::nullopt, parameter("live_t"));
    require(d.differentiability == "one_sided" && !d.right_derivative && d.left_derivative == 1 &&
        d.reason == "threshold_search_domain_boundary", "outward upper-domain derivative is unresolved while inward side remains proved");
    require(d.branch_certificate.find("\"mu_max_binary64\":\"3ff0000000000000\"") != std::string::npos, "K evidence binds original binary64 search upper endpoint");
}
void closed_singleton_t1b03_branch_certificate() {
    // Handwritten triangular profile: f(0)=f(h)=0, f(h/2)=1. This is
    // the frozen closed-threshold singleton-continuation regression geometry.
    const auto h = q(1, 16), t = q(3, 32), amplitude = q(1, 2048);
    std::vector<std::vector<Point>> faces{{{-5, 0}, {-5, h}}}, da{{{0, 0}, {0, 0}}}, dt = da;
    const std::array<int, 4> signs{-1, -1, 1, 1};
    for (int k = 1; k <= 4; ++k) {
        std::vector<Point> points, a, v;
        for (const auto y : Vector{0, h / q(2), h}) {
            const auto tooth = y == h / q(2) ? q(1) : q(0), sign = q(signs[k - 1]);
            points.push_back({q(-5 + 2 * k) + sign * (t * (y - h / q(2)) + amplitude * tooth), y});
            a.push_back({sign * tooth, 0}); v.push_back({sign * (y - h / q(2)), 0});
        }
        faces.push_back(points); da.push_back(a); dt.push_back(v);
    }
    faces.push_back({{5, 0}, {5, h}}); da.push_back({{0, 0}, {0, 0}}); dt.push_back({{0, 0}, {0, 0}});
    Model model; model.assembly.completeness = "complete"; model.assembly.pairs.emplace(); model.loads.resize(5);
    GeometrySeed2 amplitude_seed, tilt_seed; amplitude_seed.parameter = "amplitude"; tilt_seed.parameter = "tilt";
    for (std::size_t i = 0; i < 5; ++i) {
        auto ring = std::vector<Point>{faces[i][0]}, a = std::vector<Point>{da[i][0]}, v = std::vector<Point>{dt[i][0]};
        ring.insert(ring.end(), faces[i + 1].begin(), faces[i + 1].end());
        a.insert(a.end(), da[i + 1].begin(), da[i + 1].end()); v.insert(v.end(), dt[i + 1].begin(), dt[i + 1].end());
        for (std::size_t k = faces[i].size(); --k > 0;) { ring.push_back(faces[i][k]); a.push_back(da[i][k]); v.push_back(dt[i][k]); }
        const auto id = "block_" + std::to_string(i + 1); const bool fixed = i == 0 || i == 4;
        const Point origin{q(5, 8), q(-3, 8)};
        model.assembly.bodies.emplace_back(id, geom::Body(ring), origin, fixed ? "FIXED_BODY" : "", fixed ? std::array<int, 3>{0, 0, 0} : std::array<int, 3>{1, 1, 1}, origin);
        amplitude_seed.bodies.push_back({id}); tilt_seed.bodies.push_back({id});
        for (std::size_t k = 0; k < ring.size(); ++k) { amplitude_seed.vertices.push_back({id, k, a[k]}); tilt_seed.vertices.push_back({id, k, v[k]}); }
        if (i == 2) model.loads[i].live = {0, -1, origin[0]};
        for (std::size_t j = i + 1; j < 5; ++j) model.assembly.pairs->push_back({i, j});
    }
    const auto critical = critical_parameter(ct::assemble_contact_set2(model.assembly), model.loads, 1, 24);
    require(critical.exact_threshold == q(16359, 262144) && critical.attained == true, "closed singleton regression exact threshold");
    for (const auto& pair : std::vector<std::pair<GeometrySeed2, Rational>>{{amplitude_seed, q(-2043, 64)}, {tilt_seed, q(2043, 2048)}}) {
        const auto d = evaluate_sensitivity2(critical, propagate_geometry_seed2(*critical.threshold_certificate->problem, pair.first), std::nullopt, parameter(pair.first.parameter));
        slopes(d, pair.second, pair.second, "smooth", "closed singleton ray basis requires two-infinitesimal certificate");
    }
}
CriticalParameter2 two_crossings() {
    auto p = problem({{1, 0, 0}, {0, 1, 0}}, {0, 0}, {0, 0, 1}); p.mu = 1;
    const ColumnLabel2 a{ct::ContactLabel2{"a", "b", {0, 0}, "first", {0, 1}}, 1};
    const ColumnLabel2 b{ct::ContactLabel2{"a", "b", {0, 0}, "second", {0, 1}}, 1};
    CriticalBasis2 branch{"improving_ray", {0, 1}, 2, {1}, {{-1, 1}, {-1, 1}}, {a, b}, 2, {1, 1}};
    ThresholdProof2 proof; proof.exact_threshold = 1; proof.attained = true; proof.upper_basis = branch;
    proof.lower_interval = {0, 1}; proof.upper_interval = {1, 2};
    proof.upper_signs = critical_detail::branch_signs2(branch, 1, 2);
    CriticalParameter2 out; out.mathematical_status = "CERTIFIED"; out.exact_threshold = 1; out.attained = true;
    out.threshold_certificate = solve_limit_problem2(p); out.threshold_proof = std::move(proof); return out;
}
void threshold_ties_singularities_and_missing_evidence() {
    // These legacy synthetic jets do not specify raw affine primitives. Their
    // old single-basis smooth/tie claims are intentionally no longer accepted.
    auto critical = two_crossings();
    const LimitSeed2 seed{{{0, 0, 1}, {0, 0, 2}}, {0, 0}, {0, 0, 0}, "p"};
    const LimitSeed2 mu{{{0, 0, -1}, {0, 0, -1}}, {0, 0}, {0, 0, 0}, "mu"};
    for (int change = 0; change < 5; ++change) {
        auto trial = critical; auto jet = seed;
        if (change == 1) jet.dA[1][2] = 1;
        if (change == 2) trial.threshold_proof->upper_basis->determinant = {-1, 1};
        if (change == 3) trial.threshold_proof->upper_basis.reset();
        if (change == 4) trial.threshold_proof->upper_signs.reset();
        const auto result = evaluate_sensitivity2(trial, jet, mu, parameter("p"));
        require(result.differentiability == "unresolved" && !result.right_derivative && !result.left_derivative &&
            result.reason == "threshold_affine_primitives_required", "single-basis claims require complete raw-path K evidence");
    }
    auto missing = critical; missing.exact_threshold.reset();
    require(evaluate_sensitivity2(missing, seed, mu).reason == "exact_threshold_basis_and_seed_required", "bracket midpoint is not certified slope evidence");
    require(evaluate_sensitivity2(critical, LimitSeed2{}, mu).call_status == "INVALID_INPUT", "critical seed dimensions rejected");
}

void threshold_unavailable_preflight_metadata_and_order() {
    auto options = parameter("p"); options.tied_labels.push_back(std::string("unproved_label"));
    const auto critical = two_crossings();
    const LimitSeed2 seed{{{0, 0, 1}, {0, 0, 2}}, {0, 0}, {0, 0, 0}, "p"};
    auto check = [&](const SensitivityResult2& result, const std::string& reason, const std::string& status = "OK") {
        require(result.call_status == status && result.reason == reason && result.differentiability == "unresolved",
            "threshold unavailable reason and status follow referee preflight order");
        require(result.quality == "approximate" && result.method == "branch_certificate" &&
            !result.directional_derivative && !result.right_derivative && !result.left_derivative &&
            result.tied_labels.empty() && result.display_status == "NOT_APPLICABLE" && result.branch_certificate == "null",
            "unproved threshold result never claims exact jet or candidate labels");
        const auto wire = export_exact(result);
        require(wire.find("\"quality\":\"approximate\"") != std::string::npos &&
            wire.find("\"method\":\"branch_certificate\"") != std::string::npos,
            "threshold unavailable JSON retains approximate branch method");
    };
    auto missing = critical; missing.exact_threshold.reset();
    check(evaluate_sensitivity2(missing, seed, std::nullopt, options), "exact_threshold_basis_and_seed_required");
    missing = critical; missing.threshold_certificate.reset();
    check(evaluate_sensitivity2(missing, seed, std::nullopt, options), "exact_threshold_basis_and_seed_required");
    check(evaluate_sensitivity2(critical, std::nullopt, std::nullopt, options), "exact_threshold_basis_and_seed_required");
    missing.exact_threshold = q(0); missing.attained = true; missing.threshold_proof.reset();
    check(evaluate_sensitivity2(missing, seed, std::nullopt, options), "exact_threshold_basis_and_seed_required");
    options.positive_direction_valid = options.negative_direction_valid = false;
    check(evaluate_sensitivity2(missing, std::nullopt, std::nullopt, options), "no_valid_direction");
    check(evaluate_sensitivity2(critical, LimitSeed2{}, std::nullopt, options), "no_valid_direction");
    auto forbidden = seed; auto path = std::make_shared<GeometrySeed2>(); path->mu = q(1); forbidden.geometry_path = path;
    check(evaluate_sensitivity2(missing, forbidden, std::nullopt, options), "threshold_mu_seed_not_allowed", "INVALID_INPUT");
    options.positive_direction_valid = options.negative_direction_valid = true;
    check(evaluate_sensitivity2(critical, LimitSeed2{}, std::nullopt, options), "seed_shape_mismatch", "INVALID_INPUT");
    check(evaluate_sensitivity2(critical, seed, LimitSeed2{}, options), "seed_shape_mismatch", "INVALID_INPUT");
    check(evaluate_sensitivity2(critical, seed, std::nullopt, options), "threshold_affine_primitives_required");
}

Matrix left_multiply(const Matrix& transform, const Matrix& A) {
    Matrix out(transform.size(), Vector(A.empty() ? 0 : A.front().size()));
    for (std::size_t i = 0; i < transform.size(); ++i) for (std::size_t k = 0; k < A.size(); ++k)
        for (std::size_t j = 0; j < out[i].size(); ++j) out[i][j] = out[i][j] + transform[i][k] * A[k][j];
    return out;
}
Vector left_multiply(const Matrix& transform, const Vector& b) {
    Vector out(transform.size());
    for (std::size_t i = 0; i < transform.size(); ++i) for (std::size_t k = 0; k < b.size(); ++k) out[i] = out[i] + transform[i][k] * b[k];
    return out;
}
void exact_equilibrium_rotation_anchor_and_unit_metamorphics() {
    // Independent oracle differentiates three scalar diagonal fractions. Exact
    // rotation and anchor changes are invertible row maps, not rerun oracles.
    const auto p = problem({{2, 0, 0, 1, 0, 0}, {0, 3, 0, 0, 1, 0}, {0, 0, 5, 0, 0, 1}}, {3, 4, 7}, {4, 6, 10, 0, 0, 0});
    const LimitSeed2 seed{{{1, 0, 0, 0, 0, 0}, {0, 2, 0, 0, 0, 0}, {0, 0, -1, 0, 0, 0}}, {2, -1, 3}, {3, -2, 1, 0, 0, 0}, "length"};
    std::uint32_t random_state = 1729;
    for (int rotation = 0; rotation < 3; ++rotation) {
        random_state = random_state * UINT32_C(1664525) + UINT32_C(1013904223);
        const auto tangent_half = q(1 + static_cast<std::int64_t>(random_state % 19), 23);
        const auto cosine = (q(1) - tangent_half * tangent_half) / (q(1) + tangent_half * tangent_half);
        const auto sine = q(2) * tangent_half / (q(1) + tangent_half * tangent_half);
        require(cosine * cosine + sine * sine == q(1), "deterministic random rotation is exactly rigid");
      for (const auto shift : Vector{0, 1000, 100000, 1000000}) for (const auto scale : Vector{q(1, 1024), 1, 16}) {
        const Matrix transform{{cosine, -sine, 0}, {sine, cosine, 0}, {-shift, shift / q(3) + q(5, 8), scale}};
        auto moved = p; moved.A = left_multiply(transform, p.A); moved.b = left_multiply(transform, p.b);
        auto moved_seed = seed; moved_seed.dA = left_multiply(transform, seed.dA); moved_seed.db = left_multiply(transform, seed.db);
        const auto result = solve_limit_problem2(moved);
        const auto invariant = evaluate_sensitivity2(result, moved_seed, parameter("mu"));
        slopes(invariant, q(57, 10), q(57, 10), "smooth", "exact rotated equilibrium and anchor-dual covariance");
        for (auto& row : moved_seed.dA) for (auto& value : row) value = value / scale;
        for (auto& value : moved_seed.db) value = value / scale;
        for (auto& value : moved_seed.dc) value = value / scale;
        slopes(evaluate_sensitivity2(result, moved_seed, parameter("length")), q(57, 10) / scale, q(57, 10) / scale, "smooth", "length-parameter derivative follows inverse unit scale");
      }
    }
}
void g5_asymmetric_anchor_reference_metamorphic() {
    for (const Point origin : {Point{q(5, 8), q(-3, 8)}, Point{1000, -333}, Point{100000, -1024}, Point{1000000, 17}}) {
        const auto beam = g5(q(3, 2), q(5, 4), origin);
        const auto result = limit_load_ideal_exact_2d(beam.contacts, beam.loads, q(3, 8));
        slopes(evaluate_sensitivity2(result), q(5, 2), q(5, 2), "smooth", "G5 raw anchor y preserves mu derivative at large asymmetric reference");
        slopes(evaluate_sensitivity2(result, beam_seed(*result.problem, beam, "P"), parameter("P")), q(3, 4), q(3, 4), "smooth", "G5 pressure derivative independent of remote moment origin");
    }
}
void differential_stable_driver() {
    auto encode = [](const Vector& v) { std::string s = "["; for (std::size_t i = 0; i < v.size(); ++i) { if (i) s += ','; s += '"' + v[i].canonical() + '"'; } return s + ']'; };
    auto emit = [&](const char* id, const LimitProblem2& p, const LimitSeed2& seed, bool minimize) {
        const auto base = solve_limit_problem2(p); const auto result = evaluate_sensitivity2(base, seed, parameter("p"));
        std::string matrix = "["; for (std::size_t i = 0; i < seed.dA.size(); ++i) { if (i) matrix += ','; matrix += encode(seed.dA[i]); } matrix += ']';
        std::cout << "{\"id\":\"" << id << "\",\"minimize\":" << (minimize ? "true" : "false") << ",\"problem\":" << export_exact(p)
            << ",\"seed\":{\"dA\":" << matrix << ",\"db\":" << encode(seed.db) << ",\"dc\":" << encode(seed.dc)
            << "},\"base\":" << export_exact(base) << ",\"result\":" << export_exact(result)
            << ",\"result_objective\":\"maximize_c\",\"ordinary_min_derivative\":"
            << (minimize && result.right_derivative ? '"' + (-*result.right_derivative).canonical() + '"' : "null") << "}\n";
    };
    emit("stable_three_seeds", problem({{2, 1}}, {3}, {4, 0}), {{{1, 0}}, {2}, {3, 0}, "p"}, false);
    emit("stable_scaled_original_rows", problem({{2048, 1024}}, {3072}, {4, 0}), {{{1024, 0}}, {2048}, {3, 0}, "p"}, false);
    emit("stable_min_p_x1_zero", problem({{1, 1}}, {1}, {-2, 0}), {{{0, 0}}, {0}, {-1, 0}, "p"}, true);
    emit("stable_min_p_x1_nonzero", problem({{1}}, {2}, {-3}), {{{0}}, {0}, {-1}, "p"}, true);
    emit("stable_nonzero_live_column", problem({{2, 1}}, {3}, {0, 1}), {{{0, 1}}, {0}, {0, 0}, "p"}, false);
}
} // namespace
int main(int argc, char** argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--differential-stable") { differential_stable_driver(); return 0; }
        if (argc == 2 && std::string(argv[1]) == "--branch-sweep") {
            branch_faces_and_independent_beams_sweep(true);
            std::cout << "PASS branch_faces_and_independent_beams_sweep\nsensitivity: " << checks << " checks passed\n";
            return 0;
        }
        using Test = std::pair<const char*, void(*)()>;
        const std::vector<Test> tests{
            {"stable_original_unscaled_dual_three_seeds", stable_original_unscaled_dual_three_seeds},
            {"min_max_mapping_and_reverse_direction", min_max_mapping_and_reverse_direction},
            {"both_optimal_recession_guards", both_optimal_recession_guards},
            {"g5_mills_smooth_and_switch", g5_mills_smooth_and_switch},
            {"live_load_column_is_not_rhs", live_load_column_is_not_rhs},
            {"unstable_basis_cannot_hide_switch", unstable_basis_cannot_hide_switch},
            {"validity_direction_and_dimension_contracts", validity_direction_and_dimension_contracts},
            {"open_and_closed_threshold_implicit_derivatives", open_and_closed_threshold_implicit_derivatives},
            {"branch_faces_and_independent_beams", branch_faces_and_independent_beams},
            {"branch_face2_regression", branch_face2_regression},
            {"boundary_repeated_root_candidate_regression", boundary_repeated_root_candidate_regression},
            {"branch_infeasible_lower_dual_with_load_jet", branch_infeasible_lower_dual_with_load_jet},
            {"branch_pure_load_jet_corpus_regression", branch_pure_load_jet_corpus_regression},
            {"certified_shape_invariant_neutralises_witnessless_slope", certified_shape_invariant_neutralises_witnessless_slope},
            {"ordered_field_and_raw_path_guards", ordered_field_and_raw_path_guards},
            {"postfailure_candidate_singular_diagnostic", postfailure_candidate_singular_diagnostic},
            {"original_search_domain_boundary_certificate", original_search_domain_boundary_certificate},
            {"closed_singleton_t1b03_branch_certificate", closed_singleton_t1b03_branch_certificate},
            {"threshold_ties_singularities_and_missing_evidence", threshold_ties_singularities_and_missing_evidence},
            {"threshold_unavailable_preflight_metadata_and_order", threshold_unavailable_preflight_metadata_and_order},
            {"exact_equilibrium_rotation_anchor_and_unit_metamorphics", exact_equilibrium_rotation_anchor_and_unit_metamorphics},
            {"g5_asymmetric_anchor_reference_metamorphic", g5_asymmetric_anchor_reference_metamorphic}};
        bool ran = false;
        for (const auto& [name, test] : tests) if (argc == 1 || std::string(argv[1]) == name) {
            test(); ran = true; std::cout << "PASS " << name << '\n';
        }
        require(ran, "unknown named sensitivity test");
        std::cout << "sensitivity: " << checks << " checks passed\n";
        return 0;
    } catch (const std::exception& error) { std::cerr << "sensitivity failed: " << error.what() << '\n'; return 1; }
}
