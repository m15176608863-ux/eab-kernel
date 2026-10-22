#include "l1.hpp"
#include <algorithm>
#include <iostream>
#include <set>
#include <stdexcept>

using namespace eab2::contact;
namespace geom = eab2::geometry2;
namespace {
int checks = 0;
void require(bool test, const char* message) { ++checks; if (!test) throw std::runtime_error(message); }
Rational q(int n, int d = 1) { return Rational(eab2::exact::Int(n), eab2::exact::Int(d)); }
Polygon square(int x = 0, int y = 0) { return {{x, y}, {x + 1, y}, {x + 1, y + 1}, {x, y + 1}}; }
Body2 body(std::string id, Polygon ring, bool fixed = false) {
    return Body2(std::move(id), geom::Body(ring), {q(3, 8), q(-5, 8)},
        fixed ? "FIXED_BODY" : "", fixed ? std::array<int, 3>{0, 0, 0} : std::array<int, 3>{1, 1, 1});
}
Assembly2 assembly(std::vector<Body2> bodies) {
    Assembly2 a;
    a.bodies = std::move(bodies);
    a.completeness = "complete";
    a.pairs.emplace();
    for (std::size_t i = 0; i < a.bodies.size(); ++i)
        for (std::size_t j = i + 1; j < a.bodies.size(); ++j) a.pairs->push_back({i, j});
    return a;
}
Vector normalize(Vector v) {
    Rational sum;
    for (const auto& x : v) sum = sum + eab2::exact::abs(x);
    if (sum != Rational(0)) for (auto& x : v) x = x / sum;
    return v;
}
Rational dot(const Vector& a, const Vector& b) {
    require(a.size() == b.size(), "certificate dimensions");
    Rational value;
    for (std::size_t i = 0; i < a.size(); ++i) value = value + a[i] * b[i];
    return value;
}
void verify(const FirstOrderResult2& result) {
    require(result.call_status == "OK" && result.cone_is_zero.has_value(), "resolved first order");
    require(result.normalization_certificate.has_value(), "normalized proof provided");
    const auto& p = *result.normalization_certificate;
    for (const auto& x : p.exact_x) require(x >= Rational(0), "nonnegative normalized primal");
    for (std::size_t i = 0; i < p.matrix.size(); ++i) require(dot(p.matrix[i], p.exact_x) == p.rhs[i], "normalized primal equation");
    for (std::size_t j = 0; j < p.objective.size(); ++j) {
        Rational value;
        for (std::size_t i = 0; i < p.matrix.size(); ++i) value = value + p.matrix[i][j] * p.exact_y[i];
        require(value >= p.objective[j], "normalized dual inequality");
    }
    require(dot(p.objective, p.exact_x) == *result.normalized_value, "normalized primal objective");
    require(dot(p.rhs, p.exact_y) == *result.normalized_value, "normalized dual objective");
    for (const auto& row : *result.matrix)
        for (const auto& ray : *result.generators) require(dot(row, ray) >= Rational(0), "generator feasible");
    for (const auto& proof : *result.zero_certificates) {
        for (const auto& w : proof.multipliers) require(w >= Rational(0), "zero multiplier nonnegative");
        for (std::size_t k = 0; k < result.dofs.size(); ++k) {
            Rational value;
            for (std::size_t i = 0; i < result.matrix->size(); ++i) value = value + (*result.matrix)[i][k] * proof.multipliers[i];
            require(value == Rational(k == proof.coordinate ? proof.sign : 0), "zero combination exact identity");
        }
    }
}
void verify_reachability(const ConeReachability2& p) {
    if (p.unreachable) {
        require(p.multipliers.has_value() && !p.twist, "unreachable exact alternative");
        for (const auto& w : *p.multipliers) require(w >= Rational(0), "unreachable nonnegative weights");
        for (std::size_t k = 0; k < p.dofs.size(); ++k) {
            Rational value;
            for (std::size_t i = 0; i < p.matrix.size(); ++i) value = value + p.matrix[i][k] * (*p.multipliers)[i];
            require(value == Rational(0), "unreachable transpose identity");
        }
        require(dot(p.rhs, *p.multipliers) == Rational(1), "unreachable strict normalization");
    } else {
        require(p.twist.has_value() && !p.multipliers, "reachable exact alternative");
        for (std::size_t i = 0; i < p.matrix.size(); ++i) require(dot(p.matrix[i], *p.twist) >= p.rhs[i], "reachable witness exact");
    }
}
void six_regressions() {
    const auto saw = assemble_contact_set2(assembly({
        body("A", {{-2, 0}, {0, 0}, {1, 1}, {0, 2}, {-2, 2}}),
        body("B", {{0, 0}, {2, 0}, {2, 2}, {0, 2}, {1, 1}}, true)}));
    require(saw.status == "RESOLVED" && saw.segments.size() == 2 && saw.constraints.size() == 4, "regression a saw has four endpoint constraints");
    std::set<std::pair<Point, Point>> saw_normals;
    for (const auto& c : saw.constraints) {
        const auto n = c.normal(); const auto normalized = normalize({n[0], n[1]});
        saw_normals.insert({c.point, {normalized[0], normalized[1]}});
    }
    require(saw_normals == std::set<std::pair<Point, Point>>{
        {{0, 0}, {q(-1, 2), q(1, 2)}}, {{1, 1}, {q(-1, 2), q(1, 2)}},
        {{1, 1}, {q(-1, 2), q(-1, 2)}}, {{0, 2}, {q(-1, 2), q(-1, 2)}}}, "regression a analytic normals");
    const auto bare = assemble_contact_set2(assembly({body("A", square()), body("B", square(1, 1), true)}));
    require(bare.status == "MECHANICAL_UNRESOLVED" && bare.constraints.empty() && bare.unresolved.size() == 1, "regression b bare corner unresolved");
    require(first_order_mobility(bare).mathematical_status == "MECHANICAL_UNRESOLVED", "regression b no mode enumeration");
    require(bare.reachable_witnesses.size() == 1, "bare corner exact witness");
    verify_reachability(bare.reachable_witnesses[0]);
    const auto redundant = assemble_contact_set2(assembly({body("A", square()), body("B", square(1, 1), true), body("C", square(1, 0), true)}));
    require(redundant.status == "RESOLVED" && redundant.redundancy_certificates.size() == 1, "regression c twist redundancy");
    require(redundant.redundancy_certificates[0].dofs.size() == 3, "regression c rotation retained");
    verify_reachability(redundant.redundancy_certificates[0]);
    const auto flush = assemble_contact_set2(assembly({body("A", square()), body("B", square(1, 0), true)}));
    require(flush.status == "RESOLVED" && flush.constraints.size() == 2 && flush.raw_sources.size() == 8, "regression d raw endpoints are not halfplanes");
    for (const auto& c : flush.constraints) require(c.normal() == Point{-1, 0}, "regression d only interface normal");
    auto mixed = assembly({body("A", square()), body("B", {{0, 0}, {0, q(1, 2)}, {q(-1, 2), q(1, 2)},
        {-1, q(5, 4)}, {0, 1}, {q(-1, 4), 2}, {-2, 2}, {-2, 0}}, true)});
    const auto unresolved = assemble_contact_set2(mixed);
    require(unresolved.status == "MECHANICAL_UNRESOLVED" && unresolved.constraints.size() == 2 &&
        unresolved.unresolved.size() == 1 && unresolved.unresolved[0].point == Point{0, 1}, "regression e same pair edge plus true VV");
    verify_reachability(unresolved.reachable_witnesses[0]);
    for (const int anchor_x : {-1, 1}) {
        mixed.bodies[0].dof_mask = {1, 0, 1};
        mixed.bodies[0].dof_anchor = {anchor_x, 0};
        const auto cs = assemble_contact_set2(mixed);
        require(cs.status == (anchor_x == -1 ? "MECHANICAL_UNRESOLVED" : "RESOLVED"), "actual masked anchor determines VV reachability");
    }
    const auto notch = assemble_contact_set2(assembly({body("A", {{0, 0}, {2, 1}, {1, 2}}),
        body("B", {{-2, -2}, {2, -2}, {2, 0}, {0, 0}, {0, 2}, {-2, 2}}, true)}));
    require(notch.status == "RESOLVED" && notch.segments.empty() && notch.points.size() == 1 && notch.constraints.size() == 2, "regression f convex tip concave notch");
    std::set<Point> normals;
    for (const auto& c : notch.constraints) normals.insert(c.normal());
    require(normals == std::set<Point>{{2, 0}, {0, 2}}, "regression f two analytic inward normals");
}
void provenance_and_flat() {
    auto a = assembly({body("A", {{0, 0}, {1, 0}, {1, q(1, 2)}, {1, 1}, {0, 1}}), body("B", square(1, 0), true)});
    const auto flat = assemble_contact_set2(a);
    require(flat.segments.size() == 1 && flat.points.size() == 3 && flat.constraints.size() == 2, "flat interior source not force point");
    for (const auto& p : flat.points) if (p.point == Point{1, q(1, 2)}) require(!p.retained && !p.boundaries.empty() && !p.sources.empty(), "flat point retains geometric provenance");
    a.pairs->push_back({1, 0});
    const auto both = assemble_contact_set2(a);
    require(both.constraints.size() == flat.constraints.size() && both.raw_sources.size() == 2 * flat.raw_sources.size(), "bidirectional sources no double forces");
    Polygon cw = square(); std::reverse(cw.begin(), cw.end());
    const auto reversed = assemble_contact_set2(assembly({body("A", cw), body("B", square(1, 0), true)}));
    for (const auto& p : reversed.points)
        for (const auto& source : p.sources)
            if (source.kind == "VE") require(cw[source.feature_a[0]] == p.point, "original clockwise vertex ID survives");
}
void mobility_cases() {
    const auto cage = first_order_mobility(assembly({body("A", square()), body("L", square(-1), true), body("R", square(1), true),
        body("T", square(0, 1), true), body("B", square(0, -1), true)}));
    verify(cage);
    require(cage.cone_is_zero == true && cage.exact_rank == 3 && cage.zero_certificates->size() == 6, "cage full-rank zero cone");
    const auto seam = first_order_mobility(assembly({body("A", square()), body("L", square(-1), true), body("R", square(1), true)}));
    verify(seam);
    require(seam.cone_is_zero == false && seam.exact_rank == 2 && seam.normalized_value == Rational(0), "rank is necessary despite zero normalized objective");
    require(std::set<Vector>(seam.generators->begin(), seam.generators->end()) == std::set<Vector>{{0, -1, 0}, {0, 1, 0}}, "seam both line signs");
    const auto free = first_order_mobility(assembly({body("A", square())}));
    verify(free);
    require(free.lineality->size() == 3 && free.generators->size() == 6, "unconstrained three bidirectional twists");
    const auto fixed = first_order_mobility(assembly({body("A", square(), true)}));
    verify(fixed);
    require(fixed.cone_is_zero == true && fixed.dofs.empty() && fixed.zero_certificates->empty(), "zero-dimensional cone");
    auto unknown = assembly({body("A", square())}); unknown.completeness = "completeness_unknown";
    require(first_order_mobility(unknown).mathematical_status == "UNPROVED", "unknown completeness not a boolean");
    require(first_order_mobility(assembly({body("A", square()), body("B", square(), true)})).mathematical_status == "OVERLAP", "overlap refuses mobility conclusion");
    auto plate = assembly({body("A", square()), body("L", square(-1), true)});
    plate.bodies[0].boundary_type = "FORCE_CONTROLLED_PLATE";
    plate.bodies[0].dof_mask = {1, 0, 1}; plate.bodies[0].dof_anchor = {0, q(1, 2)};
    const auto result = first_order_mobility(plate); verify(result);
    require(std::set<Vector>(result.rays->begin(), result.rays->end()) == std::set<Vector>{{q(1, 3), q(-2, 3)}, {q(1, 3), q(2, 3)}}, "plate rotation at actual anchor not load reference");
    const auto multi = first_order_mobility(assembly({body("A", square()), body("B", square(1))}));
    verify(multi);
    require(multi.dofs.size() == 6 && multi.cone_is_zero == false, "two freely moving bodies six coordinates");
}
void lock_cases() {
    const geom::Body moving(square());
    const auto separate = query_lock(moving, {geom::Body(square(1))});
    require(separate.status == "REMOVABLE_TRANSLATION" && separate.separation_ray.has_value() && !separate.refinement, "removable lock has exact ray only");
    // The two CCW squares each have two original ears. Their four Cartesian
    // products have three zero-incident cells and thirteen nonincident edges;
    // the nearest diagonal edge has squared distance 1/2, hence r=1/3.
    // Merging changes these exact witnesses despite preserving E/O states.
    require(separate.local_cells.size() == 3 && separate.radius_bounds.size() == 13 && separate.arcs.size() == 12,
        "lock keeps unmerged ear-product cell witnesses");
    require(separate.local_cells[0].cell_index == 0 && separate.local_cells[1].cell_index == 2 && separate.local_cells[2].cell_index == 3,
        "lock original Cartesian ear indices");
    require(separate.radius == q(1, 3), "lock unmerged diagonal edge gives exact one-third radius");
    const auto seam = query_lock(moving, {geom::Body(square(-1)), geom::Body(square(1))});
    require(seam.status == "NOT_SEPARABLE_TRANSLATION" && seam.refinement == "SEAM_SLIDING" && seam.seam_ray.has_value(), "pairwise removable union has seam");
    const auto cage = query_lock(moving, {geom::Body(square(-1)), geom::Body(square(1)), geom::Body(square(0, -1)), geom::Body(square(0, 1))});
    require(cage.refinement == "TRANSLATION_IMMOBILE" && !cage.seam_ray, "translation cage immobile");
    require(query_lock(moving, {}).status == "NOT_CONTACT", "no neighbors not contact");
    const auto outside = query_lock(moving, {geom::Body(square(8))});
    require(outside.status == "NOT_CONTACT" && outside.contact_sources.empty() && !outside.radius_bounds.empty(), "outside neighbor included only exclusion radius");
    const auto overlap = query_lock(moving, {moving});
    require(!overlap.status && overlap.mathematical_status == "OVERLAP" && !overlap.radius, "overlap refuses lock signing");
    for (const auto& result : {separate, seam, cage, outside}) {
        require(result.radius > Rational(0), "strict positive rational radius");
        for (const auto& bound : result.radius_bounds) require(*result.radius * *result.radius < bound.squared_distance, "radius strict edge inequality");
        for (const auto& arc : result.arcs) {
            // Independent finite probe uses direct polygon intersection, not
            // the lock active-edge classifier or its product-cell union.
            const auto step = *result.radius / Rational(2);
            const auto direction = geom::mul(arc.sample, step);
            int state = -1;
            const std::vector<geom::Body> walls = result.status == "NOT_CONTACT" ? std::vector<geom::Body>{geom::Body(square(8))} :
                result.refinement == "TRANSLATION_IMMOBILE" ? std::vector<geom::Body>{geom::Body(square(-1)), geom::Body(square(1)), geom::Body(square(0, -1)), geom::Body(square(0, 1))} :
                result.refinement == "SEAM_SLIDING" ? std::vector<geom::Body>{geom::Body(square(-1)), geom::Body(square(1))} : std::vector<geom::Body>{geom::Body(square(1))};
            for (const auto& wall : walls) state = std::max(state, geom::polygons_overlap_exact(moving, wall, direction));
            require(arc.state == (state == 1 ? "PENETRATING" : state == 0 ? "CONTACT" : "SEPARATING"), "lock sector independent polygon oracle");
        }
    }
}
// Independent cofactor polynomial oracle for pointed 3-D rational cones.
std::set<Vector> cofactor_rays(const Matrix& rows) {
    std::set<Vector> out;
    for (std::size_t i = 0; i < rows.size(); ++i) for (std::size_t j = i + 1; j < rows.size(); ++j) {
        const auto& a = rows[i]; const auto& b = rows[j];
        const Vector cross{a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
        if (cross == Vector(3)) continue;
        for (const int sign : {-1, 1}) {
            auto candidate = cross; for (auto& v : candidate) v = v * Rational(sign);
            if (std::all_of(rows.begin(), rows.end(), [&](const auto& row) { return dot(row, candidate) >= Rational(0); })) out.insert(normalize(candidate));
        }
    }
    return out;
}
void dd_oracle() {
    std::uint32_t state = 654321;
    for (int example = 0; example < 32; ++example) {
        Matrix rows{{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
        for (int k = 0; k < 5; ++k) {
            Vector row;
            for (int j = 0; j < 3; ++j) { state = state * 1664525U + 1013904223U; row.push_back(Rational(static_cast<int>(state % 7) - 3)); }
            rows.push_back(row);
        }
        const auto [rays, lines] = double_description(rows, 3);
        require(lines.empty(), "pointed cofactor example");
        require(std::set<Vector>(rays.begin(), rays.end()) == cofactor_rays(rows), "DD equals independent cofactor polynomial rays");
        std::reverse(rows.begin(), rows.end());
        rows.push_back(rows[0]);
        const auto reordered = double_description(rows, 3);
        require(std::set<Vector>(reordered.first.begin(), reordered.first.end()) == std::set<Vector>(rays.begin(), rays.end()), "DD redundant row/order invariant");
    }
}
Point transformed(const Point& p, int rotation, bool reflect, const Rational& scale, const Point& translation) {
    Point v = p;
    if (reflect) v[0] = -v[0];
    for (int i = 0; i < rotation; ++i) v = {-v[1], v[0]};
    return {scale * v[0] + translation[0], scale * v[1] + translation[1]};
}
void exact_metamorphic() {
    const auto base = assembly({body("A", square()), body("L", square(-1), true), body("B", square(0, -1), true)});
    const auto original = first_order_mobility(base); verify(original);
    require(original.lineality->empty(), "metamorphic cone pointed to make ray set canonical");
    for (int rotation = 0; rotation < 4; ++rotation) for (const bool reflection : {false, true})
        for (const auto scale : {q(1, 8), q(1), q(8)}) {
            const Point translation{q(100000) + q(3, 8), q(-1000) + q(5, 16)};
            std::vector<Body2> bodies;
            for (const auto& old : base.bodies) {
                Polygon ring;
                for (const auto& p : old.geometry.vertices) ring.push_back(transformed(p, rotation, reflection, scale, translation));
                bodies.emplace_back(old.body_id, geom::Body(ring), transformed(old.reference_point, rotation, reflection, scale, translation),
                    old.boundary_type, old.dof_mask, transformed(old.dof_anchor, rotation, reflection, scale, translation));
            }
            const auto changed = first_order_mobility(assembly(std::move(bodies))); verify(changed);
            require(changed.mathematical_status == original.mathematical_status, "exact rigid/unit status invariant");
            std::set<Vector> expected;
            for (const auto& r : *original.generators) {
                const auto xy = transformed({r[0], r[1]}, rotation, reflection, scale, {0, 0});
                expected.insert(normalize({xy[0], xy[1], r[2] * Rational(reflection ? -1 : 1)}));
            }
            require(std::set<Vector>(changed.generators->begin(), changed.generators->end()) == expected, "exact rigid/unit generator covariance");
            auto map_polygon = [&](const Polygon& polygon) {
                Polygon mapped;
                for (const auto& p : polygon) mapped.push_back(transformed(p, rotation, reflection, scale, translation));
                return geom::Body(mapped);
            };
            const auto moving = map_polygon(square());
            auto walls = std::vector<geom::Body>{map_polygon(square(-1)), map_polygon(square(1))};
            const auto seam = query_lock(moving, walls);
            require(seam.status == "NOT_SEPARABLE_TRANSLATION" && seam.refinement == "SEAM_SLIDING", "exact rigid/unit seam classification");
            walls.push_back(map_polygon(square(0, -1))); walls.push_back(map_polygon(square(0, 1)));
            const auto cage = query_lock(moving, walls);
            require(cage.refinement == "TRANSLATION_IMMOBILE", "exact rigid/unit cage classification");
            for (const auto& bound : seam.radius_bounds) require(*seam.radius * *seam.radius < bound.squared_distance, "transformed strict radius");
        }
}
void resource_guards() {
    auto input = assembly({body("A", square()), body("B", square(1), true)});
    input.limits.max_elements = 1;
    bool limited = false;
    try { (void)assemble_contact_set2(input); }
    catch (const eab2::numeric::Error& error) { limited = error.code == 5; }
    require(limited, "L1 assembly count resource limit fails loud");
    const auto contact = assemble_contact_set2(assembly({body("A", square()), body("B", square(1), true)}));
    auto small = contact; small.assembly.limits.max_elements = 10;
    limited = false;
    try { (void)first_order_mobility(small); }
    catch (const eab2::exact::ResourceLimit&) { limited = true; }
    require(limited, "L1 normalized matrix resource limit fails loud");
}
} // namespace
int main() {
    try {
        six_regressions(); provenance_and_flat(); mobility_cases(); lock_cases(); dd_oracle(); exact_metamorphic(); resource_guards();
        std::cout << "EAB2_L1_TESTS checks=" << checks << " failed=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "EAB2_L1_TESTS checks=" << checks << " failed=1 detail=" << error.what() << '\n';
        return 1;
    }
}
