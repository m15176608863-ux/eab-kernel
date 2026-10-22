#include "geometry2.hpp"
#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <string>

using namespace eab2::geometry2;
namespace {
std::size_t checks = 0;
void check(bool condition, const char* name) {
    ++checks;
    if (!condition) throw std::runtime_error(name);
}
template<class F> void invalid(F action, const char* name) {
    ++checks;
    try { action(); }
    catch (const std::invalid_argument&) { return; }
    throw std::runtime_error(name);
}
template<class F> void resource(F action, const char* name) {
    ++checks;
    try { action(); }
    catch (const eab2::numeric::Error& error) { if (error.code == 5) return; throw; }
    catch (const eab2::exact::ResourceLimit&) { return; }
    throw std::runtime_error(name);
}
Rational fraction(std::int64_t n, std::int64_t d) { return Rational(Int(n), Int(d)); }
const Polygon square{{0, 0}, {1, 0}, {1, 1}, {0, 1}};
const Polygon elbow{{0, 0}, {3, 0}, {3, 1}, {1, 1}, {1, 3}, {0, 3}};
const Polygon channel{{-1, -1}, {2, -1}, {2, 2}, {1, 2}, {1, 0}, {0, 0}, {0, 2}, {-1, 2}};
const Polygon pin{{0, fraction(1, 2)}, {1, fraction(1, 2)}, {1, fraction(3, 2)}, {0, fraction(3, 2)}};
const Polygon pocket{{0, 0}, {6, 0}, {6, 2}, {5, 2}, {5, 1}, {1, 1}, {1, 5}, {5, 5}, {5, 4}, {6, 4}, {6, 6}, {0, 6}};
const Polygon plug{{1, 1}, {5, 1}, {5, 5}, {1, 5}};

// Independent rectangular interval oracle. It uses neither production hull,
// ears, segment arrangement nor any production point/vector predicate.
int interval_rectangle(const Point& p, std::int64_t xmax, std::int64_t ymax) {
    if (p[0] < Rational(-1) || p[0] > Rational(xmax) || p[1] < Rational(-1) || p[1] > Rational(ymax)) return -1;
    return p[0] == Rational(-1) || p[0] == Rational(xmax) || p[1] == Rational(-1) || p[1] == Rational(ymax) ? 0 : 1;
}
int elbow_oracle(const Point& p) { return std::max(interval_rectangle(p, 3, 1), interval_rectangle(p, 1, 3)); }
void validation_and_ids() {
    invalid([] { Body body({{0, 0}, {1, 0}}); }, "fewer than three");
    invalid([] { Body body({{0, 0}, {1, 0}, {1, 0}, {0, 1}}); }, "zero edge");
    invalid([] { Body body({{0, 0}, {1, 0}, {2, 0}}); }, "zero area");
    invalid([] { Body body({{0, 0}, {2, 0}, {1, 0}, {1, 1}, {0, 1}}); }, "backtracking");
    invalid([] { Body body({{0, 0}, {2, 2}, {0, 2}, {2, 0}}); }, "self crossing");
    invalid([] { Body body({{0, 0}, {2, 0}, {2, 2}, {1, 0}, {0, 2}}); }, "nonadjacent touch");
    const Polygon flat{{0, 0}, {fraction(1, 2), 0}, {1, 0}, {1, 1}, {0, 1}};
    Body body(flat);
    check(body.vertices == flat && body.vertices.size() == 5, "flat vertex retained");
    check(body.original_vertex_ids == std::vector<std::size_t>{0, 1, 2, 3, 4}, "ccw vertex ids");
    auto cw = flat; std::reverse(cw.begin(), cw.end()); const Body reverse(cw);
    check(reverse.vertices == flat, "cw normalized");
    check(reverse.original_vertex_ids == std::vector<std::size_t>{4, 3, 2, 1, 0}, "cw original vertex ids");
    check(reverse.original_edge_ids == std::vector<std::size_t>{3, 2, 1, 0, 4}, "cw original edge ids");
    const auto bits_body = Body::from_bits({{UINT64_C(0x8000000000000000), 0}, {UINT64_C(0x3ff0000000000000), 0},
        {0, UINT64_C(0x3ff0000000000000)}});
    check(bits_body.vertices[0][0] == Rational(0) && bits_body.input_bits[0][0] == UINT64_C(0x8000000000000000), "negative zero provenance");
    bool nonfinite = false;
    try { Body::from_bits({{UINT64_C(0x7ff0000000000000), 0}, {UINT64_C(0x3ff0000000000000), 0}, {0, UINT64_C(0x3ff0000000000000)}}); }
    catch (const eab2::numeric::Error& error) { nonfinite = error.code == 1; }
    check(nonfinite, "nonfinite bits rejected");
    check(convexity_violation(flat).empty(), "flat convexity");
    check(!convexity_violation(elbow).empty(), "concave violates convexity");
}
void convex_and_covers() {
    const auto entrance = entrance_block_exact(square, square);
    check(entrance.facets.size() == 4, "parallel edges merge FF");
    for (const auto& facet : entrance.facets) check(facet.label.kind == "FF", "parallel FF source");
    check(membership_exact(entrance, {0, 0}) == 1, "convex interior");
    check(membership_exact(entrance, {1, 0}) == 0, "convex contact");
    check(membership_exact(entrance, {2, 0}) == -1, "convex outside");
    const Polygon flat{{0, 0}, {fraction(1, 2), 0}, {1, 0}, {1, 1}, {0, 1}};
    check(entrance_block_exact(flat, square).vertices.size() == 5, "convex Minkowski flat facet preserved");
    invalid([] { entrance_block_exact(elbow, square); }, "concave rejected by convex-only API");
    for (std::size_t i = 0; i < square.size(); ++i) for (std::size_t j = 0; j < square.size(); ++j) {
        const auto ve = ve_cover(square, i, square, j), ev = ev_cover(square, i, square, j);
        check(bool(ve) == (ve_side_exact(square, i, square, j) >= 0), "VE exact cone consistency");
        check(bool(ev) == (ev_side_exact(square, i, square, j) >= 0), "EV exact cone consistency");
        if (ve) {
            check(ve->param.has_value() && ve->gap_squared >= Rational(0), "VE exact recipes");
            check(dot(sub(ve->point_a, ve->point_b), sub(ve->point_a, ve->point_b)) == ve->gap_squared, "VE witness metric");
        }
    }
    auto shifted = square; for (auto& p : shifted) p = add(p, {2, 2});
    const auto vv = vv_cover(shifted, 0, square, 2);
    check(vv.has_value() && vv->strict && vv->gap_squared == Rational(2), "VV active diagonal");
    auto touching = square; for (auto& p : touching) p = add(p, {1, 1});
    const auto coincident = vv_cover(touching, 0, square, 2);
    check(coincident.has_value() && coincident->strict && !coincident->normal_direction, "VV coincident no normal");
    check(enumerate_covers(touching, square, Rational(0)).size() == 5, "zero-window endpoint VE EV VV associations");
    check(enumerate_covers(touching, square, Rational(-1)).empty(), "negative window empty");
    check(vertex_side_exact(flat, 1, {-1, 0}) == 0 && vertex_side_exact(flat, 1, {1, 0}) == -1, "flat vertex cone ray direction");
    const auto eps = fraction(1, 1024);
    const Polygon tip{{-eps, fraction(5, 4)}, {fraction(1, 4), fraction(3, 2)}, {-fraction(1, 4), fraction(3, 2)}};
    const auto has = [](const std::vector<Cover>& covers, const Label& label) {
        return std::any_of(covers.begin(), covers.end(), [&](const Cover& c) { return c.label == label; });
    };
    check(!has(enumerate_covers(tip, square, Rational(1)), {"VE", 0, 2}), "exact segment rejects outside projection");
    check(has(enumerate_covers(tip, square, Rational(1), true, Rational(0), std::nullopt, eps * Rational(2)), {"VE", 0, 2}), "explicit segment window accepts exact squared bound");
    check(has(enumerate_covers(tip, square, Rational(1), false), {"VE", 0, 2}), "segment clipping optional");
    const Polygon triangle{{0, 0}, {-1, 1}, {-1, -1}};
    auto offset = square; for (auto& p : offset) p = add(p, {eps, -eps / Rational(16)});
    const auto small = vv_cover(offset, 0, triangle, 0, Rational(0), fraction(1, 32));
    const auto wide = vv_cover(offset, 0, triangle, 0, Rational(0), fraction(1, 8));
    check(small && wide && !small->strict && !wide->strict && !small->window_active && wide->window_active, "VV explicit window does not promote exact strictness");
    const Polygon reflex{{0, 0}, {1, 0}, {1, 1}, {0, 1}, {eps, fraction(1, 2)}};
    const Polygon neighbor{{-1, 0}, {0, 0}, {0, 1}, {-1, 1}};
    check(!ve_cover(reflex, 4, neighbor, 1), "true reflex rejected without window");
    const auto relaxed = ve_cover(reflex, 4, neighbor, 1, Rational(0), fraction(1, 4));
    check(relaxed && !relaxed->strict, "explicit cone admits small reflex but never strict");
    check(enumerate_covers(tip, square, std::nullopt).size() >= enumerate_covers(tip, square, Rational(1)).size(), "unbounded distance window");
}
void concavity_and_strata() {
    Entrance entry(Body(square), Body(elbow), true, true);
    check(entry.parts_a.size() == 1 && entry.parts_b.size() == 2, "certified convex merging");
    check(!entry.subdivision_is_materialized(), "construction lazy");
    for (int x = -4; x <= 8; ++x) for (int y = -4; y <= 8; ++y) {
        const Point point{fraction(x, 2), fraction(y, 2)};
        check(entry.membership(point) == elbow_oracle(point), "nonconvex exact rectangle-union oracle");
    }
    check(entry.membership({2, 2}) == -1, "concavity not replaced by hull");
    check(polygons_overlap_exact(Body(square), Body(elbow), {2, 2}) == -1, "polygon overlap wrapper");
    check(entrance_membership_exact(Body(square), Body(elbow), {3, 0}) == 0, "topology wrapper");
    for (const auto& e : entry.contact_segments()) {
        const auto p = mul(add(e.start, e.end), fraction(1, 2));
        check(elbow_oracle(p) == 0, "contact skeleton independently labelled");
        check(!e.labels.empty(), "contact source label retained");
        check(e.boundary == (entry.topology(p) == 0), "boundary by tangent occupancy");
    }
    const auto& subdivision = entry.subdivision();
    check(subdivision.vertices.size() + subdivision.faces.size() == subdivision.edges.size() + 1, "subdivision Euler");
    for (const auto* layer : {&subdivision.vertices, &subdivision.edges, &subdivision.faces}) for (const auto& c : *layer)
        check(c.body_state == elbow_oracle(c.sample), "every exported stratum exact independent oracle");
    for (const auto& c : entry.clipped_covers()) {
        check(c.body_state == elbow_oracle(mul(add(c.start, c.end), fraction(1, 2))), "clipped cover body state");
        check(c.exposed == ((c.side_states[0] >= 0) != (c.side_states[1] >= 0)), "clipped cover occupancy");
    }
    const auto json = entry.export_exact();
    check(json.find("eab2.c1.exact.v1") != std::string::npos && json.find("\"raw_segments\"") != std::string::npos, "exact export schema");
}
void tight_contacts() {
    Entrance seam{Body(pin), Body(channel)};
    check(seam.membership({0, 0}) == 0 && seam.topology({0, 0}) == 1, "seam body and topology differ");
    check(seam.directional_state({0, 0}, {0, 1}) == 0 && seam.directional_state({0, 0}, {1, 0}) == 1, "seam tangent states");
    bool inner = false;
    for (const auto& e : seam.contact_segments()) if (on_segment({0, 0}, e.start, e.end)) inner = inner || !e.boundary;
    check(inner, "unfiltered raw contacts preserve inner seam");
    Entrance isolated{Body(plug), Body(pocket)};
    check(isolated.membership({0, 0}) == 0 && isolated.topology({0, 0}) == 1, "isolated contact interior E");
    bool point = false;
    for (const auto& p : isolated.contact_points()) point = point || p.point == Point{0, 0};
    check(point, "isolated contact retained");
    for (const auto& e : isolated.contact_segments()) check(!on_segment({0, 0}, e.start, e.end), "isolated fixture no incident contact open edge");
    point = false;
    for (const auto& c : isolated.subdivision().vertices) point = point || (c.sample == Point{0, 0} && c.body_state == 0);
    check(point, "isolated contact inserted into event wall");
}
void determinism_and_exact_transforms() {
    Entrance base{Body(square), Body(elbow)};
    Entrance full(Body(square), Body(elbow), false, false);
    (void)full.subdivision();
    auto reversed = elbow; std::reverse(reversed.begin(), reversed.end());
    auto cyclic = square; std::rotate(cyclic.begin(), cyclic.begin() + 1, cyclic.end());
    Entrance permuted{Body(cyclic), Body(reversed)};
    Entrance swapped{Body(elbow), Body(square)};
    for (int x = -2; x <= 6; ++x) for (int y = -2; y <= 6; ++y) {
        const Point p{fraction(x, 2), fraction(y, 2)};
        check(base.membership(p) == full.membership(p) && base.topology(p) == full.topology(p), "merge compact flags preserve state");
        check(base.membership(p) == permuted.membership(p) && base.topology(p) == permuted.topology(p), "ring direction start invariance");
        check(base.membership(p) == swapped.membership(mul(p, Rational(-1))), "body order antisymmetry");
    }
    for (const int exponent : {-400, 0, 400}) {
        const Rational scale = exponent >= 0 ? Rational(Int(1) << static_cast<std::size_t>(exponent))
                                             : Rational(Int(1), Int(1) << static_cast<std::size_t>(-exponent));
        const Point ta{1000000, -3000}, tb{-2000, 4000};
        auto transform = [&](const Polygon& p, const Point& t) { Polygon q; for (const auto& x : p) q.push_back(add(mul(Point{-x[1], x[0]}, scale), t)); return q; };
        Entrance moved(Body(transform(square, ta)), Body(transform(elbow, tb)));
        for (const Point p : {Point{0, 0}, Point{3, 0}, Point{2, 2}, Point{-1, -1}}) {
            const auto q = add(mul(Point{-p[1], p[0]}, scale), sub(tb, ta));
            check(moved.membership(q) == base.membership(p) && moved.topology(q) == base.topology(p), "exact rotation scale huge translation");
        }
    }
    Entrance before{Body(square), Body(elbow)}, after{Body(square), Body(elbow)};
    (void)before.membership({0, 0}); const auto first = before.export_exact();
    (void)after.subdivision(); (void)after.membership({0, 0});
    check(first == after.export_exact(), "query order exact serialization deterministic");
}
void configurable_limits_and_transactions() {
    GeometryLimits limits;
    limits.max_elements = 3;
    resource([&] { Body body(square, limits); }, "configured body element bound");
    limits = {}; limits.max_integer_bits = 3;
    resource([&] { Body body({{0, 0}, {8, 0}, {0, 8}}, limits); }, "configured input integer bit bound");
    limits = {}; limits.max_work_units = 1;
    resource([&] { Body body(square, limits); }, "configured validation work bound");
    const Body body(square);
    resource([&] { Entrance entry(body, body, true, true, limits); }, "configured product construction work bound");
    Entrance entry(body, body);
    resource([&] { GeometryWorkScope scope(limits); entry.membership({0, 0}); }, "outer batch scope charges nested queries");
    check(entry.membership({0, 0}) == 1, "resource scope restores unrelated future query");
    limits.max_work_units = 4;
    resource([&] { GeometryWorkScope scope(limits); (void)entry.raw_segments(); }, "raw materialization aborts internally");
    check(entry.raw_segments().size() == 32, "failed raw materialization never publishes partial cache");
    for (const std::uint64_t cap : {UINT64_C(1), UINT64_C(40), UINT64_C(400)}) {
        Entrance partial(body, body);
        limits.max_work_units = cap;
        resource([&] { GeometryWorkScope scope(limits); (void)partial.export_exact(); }, "partial global construction aborts");
        check(!partial.subdivision_is_materialized(), "failed low-budget export has no committed subdivision");
        resource([&] { GeometryWorkScope scope(limits); (void)partial.export_exact(); }, "same low-budget retry must not bypass limits via partial cache");
        const auto& subdivision = partial.subdivision();
        check(subdivision.vertices.size() + subdivision.faces.size() == subdivision.edges.size() + 1, "later adequate budget rebuilds complete subdivision");
        check(partial.membership({0, 0}) == 1 && partial.membership({1, 0}) == 0, "retry retains exact labels");
    }
    const auto json = entry.export_exact();
    check(json.find("\"limits\":{\"max_work_units\":50000000,\"max_elements\":2000000,\"max_integer_bits\":65536}") != std::string::npos,
          "exact export echoes frozen limits");
}
} // namespace
int main() {
    try {
        validation_and_ids(); convex_and_covers(); concavity_and_strata(); tight_contacts(); determinism_and_exact_transforms(); configurable_limits_and_transactions();
        std::cout << "EAB2_GEOMETRY2_TESTS checks=" << checks << " failed=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "EAB2_GEOMETRY2_TESTS checks=" << checks << " failed=1 detail=" << error.what() << '\n';
        return 1;
    }
}
