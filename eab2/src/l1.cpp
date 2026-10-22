#include "l1.hpp"
#include "geometry2_local.hpp"
#include <algorithm>
#include <map>
#include <set>
#include <sstream>
#include <tuple>

namespace eab2::contact {
namespace {
using geometry2::add;
using geometry2::sub;
using geometry2::mul;
using geometry2::cross;
using geometry2::dot;
using geometry2::on_segment;
using geometry2::GeometryWorkScope;
void check_matrix_size(GeometryWorkScope& work, std::size_t rows, std::size_t columns) {
    work.check_size(rows);
    work.check_size(columns);
    if (columns && rows > work.limits.max_elements / columns)
        throw exact::ResourceLimit("L1 matrix element limit exceeded");
}
Point neg(const Point& p) { return {-p[0], -p[1]}; }
Point rot(const Point& p) { return {-p[1], p[0]}; }
Point ray(const Point& p) {
    const Rational scale = exact::abs(p[0]) + exact::abs(p[1]);
    if (scale == Rational(0)) throw std::logic_error("zero angular direction");
    return mul(p, Rational(1) / scale);
}
bool angle_less(const Point& a, const Point& b) {
    const int ha = a[1] > Rational(0) || (a[1] == Rational(0) && a[0] > Rational(0)) ? 0 : 1;
    const int hb = b[1] > Rational(0) || (b[1] == Rational(0) && b[0] > Rational(0)) ? 0 : 1;
    return ha != hb ? ha < hb : cross(a, b) > Rational(0);
}
Rational vdot(const Vector& a, const Vector& b) {
    if (a.size() != b.size()) throw std::invalid_argument("vector width mismatch");
    Rational result;
    for (std::size_t k = 0; k < a.size(); ++k) result = result + a[k] * b[k];
    return result;
}
Vector vneg(Vector v) { for (auto& x : v) x = -x; return v; }
std::size_t rank(Matrix rows, std::size_t size) {
    GeometryWorkScope work;
    check_matrix_size(work, rows.size(), size);
    for (const auto& row : rows)
        if (row.size() != size) throw std::invalid_argument("matrix width mismatch");
    std::size_t result = 0;
    for (std::size_t col = 0; col < size; ++col) {
        std::size_t pivot = result;
        while (pivot < rows.size() && rows[pivot][col] == Rational(0)) ++pivot;
        if (pivot == rows.size()) continue;
        std::swap(rows[result], rows[pivot]);
        const Rational factor = rows[result][col];
        for (auto& value : rows[result]) value = value / factor;
        for (std::size_t i = result + 1; i < rows.size(); ++i) {
            const Rational f = rows[i][col];
            if (f == Rational(0)) continue;
            for (std::size_t k = 0; k < size; ++k) {
                work.step();
                rows[i][k] = rows[i][k] - f * rows[result][k];
            }
        }
        ++result;
    }
    return result;
}
Matrix unique_rays(const Matrix& values) {
    std::set<Vector> unique;
    for (auto value : values) {
        Rational size;
        for (const auto& x : value) size = size + exact::abs(x);
        if (size == Rational(0)) continue;
        for (auto& x : value) x = x / size;
        unique.insert(std::move(value));
    }
    return {unique.begin(), unique.end()};
}
std::vector<Point> halfplane(const Point& edge) { return {edge, neg(edge), rot(edge)}; }
std::vector<std::vector<Point>> material_pieces(const Polygon& polygon, const Point& p) {
    for (std::size_t i = 0; i < polygon.size(); ++i) {
        if (polygon[i] != p) continue;
        const Point before = sub(p, polygon[(i + polygon.size() - 1) % polygon.size()]);
        const Point after = sub(polygon[(i + 1) % polygon.size()], p);
        const int turn = cross(before, after).sign();
        if (turn > 0) return {{after, neg(before)}};
        if (turn == 0) return {halfplane(after)};
        return {halfplane(before), halfplane(after)};
    }
    for (std::size_t i = 0; i < polygon.size(); ++i)
        if (on_segment(p, polygon[i], polygon[(i + 1) % polygon.size()]))
            return {halfplane(sub(polygon[(i + 1) % polygon.size()], polygon[i]))};
    throw std::invalid_argument("point is not on polygon boundary");
}
std::vector<Point> cone_normals(const std::vector<Point>& generators) {
    std::map<Point, Point> normals;
    for (const auto& g : generators) {
        for (const auto& n : std::array<Point, 2>{rot(g), neg(rot(g))}) {
            if (std::all_of(generators.begin(), generators.end(), [&](const Point& h) { return dot(n, h) >= Rational(0); }))
                normals.emplace(ray(n), n);
        }
    }
    std::vector<Point> out;
    for (const auto& entry : normals) out.push_back(entry.second);
    return out;
}
std::vector<Point> samples(const std::vector<Point>& normals) {
    std::set<Point> directions;
    for (const auto& n : normals) {
        directions.insert(ray(rot(n)));
        directions.insert(ray(neg(rot(n))));
    }
    std::vector<Point> rays(directions.begin(), directions.end());
    std::sort(rays.begin(), rays.end(), angle_less);
    std::vector<Point> out = rays;
    for (std::size_t i = 0; i < rays.size(); ++i) {
        const auto& a = rays[i];
        const auto& b = rays[(i + 1) % rays.size()];
        out.push_back(cross(a, b) > Rational(0) ? add(a, b) : rot(a));
    }
    return out;
}
bool free_direction(const std::vector<std::vector<Point>>& forbidden, const Point& d) {
    return !std::any_of(forbidden.begin(), forbidden.end(), [&](const auto& cone) {
        return std::all_of(cone.begin(), cone.end(), [&](const Point& n) { return dot(n, d) > Rational(0); });
    });
}
void point_cone(ContactPoint2& point, const Polygon& pa, const Polygon& pb) {
    for (const auto& ca : material_pieces(pa, point.point)) {
        for (auto cb : material_pieces(pb, point.point)) {
            for (const auto& p : ca) cb.push_back(neg(p));
            const auto normals = cone_normals(cb);
            if (std::find(point.forbidden.begin(), point.forbidden.end(), normals) == point.forbidden.end())
                point.forbidden.push_back(normals);
        }
    }
    std::vector<Point> all;
    for (const auto& cone : point.forbidden) all.insert(all.end(), cone.begin(), cone.end());
    const auto directions = samples(all);
    std::vector<Point> free;
    for (const auto& d : directions) if (free_direction(point.forbidden, d)) free.push_back(d);
    std::map<Point, Point> kept;
    for (const auto& n : all) {
        const Point normal = neg(n);
        if (!free.empty() &&
            std::all_of(free.begin(), free.end(), [&](const Point& d) { return dot(normal, d) >= Rational(0); }) &&
            std::any_of(free.begin(), free.end(), [&](const Point& d) { return dot(normal, d) == Rational(0); }))
            kept.emplace(ray(normal), normal);
    }
    for (const auto& entry : kept) point.boundaries.push_back(entry.second);
    const bool convex = !free.empty() && std::all_of(directions.begin(), directions.end(), [&](const Point& d) {
        return free_direction(point.forbidden, d) ==
            std::all_of(point.boundaries.begin(), point.boundaries.end(), [&](const Point& n) { return dot(n, d) >= Rational(0); });
    });
    point.fp_type = convex ? "CONVEX" : "TRUE_VV";
}
using PointSources = std::map<Point, std::set<Source2>>;
void raw_pair(PointSources& result, const Body2& a, const Body2& b) {
    GeometryWorkScope work;
    const auto& pa = a.geometry.vertices;
    const auto& pb = b.geometry.vertices;
    const auto& ia = a.geometry.original_vertex_ids;
    const auto& ib = b.geometry.original_vertex_ids;
    for (std::size_t i = 0; i < pa.size(); ++i) {
        for (std::size_t j = 0; j < pb.size(); ++j) {
            work.step();
            const auto in = (i + 1) % pa.size(), jn = (j + 1) % pb.size();
            if (on_segment(pa[i], pb[j], pb[jn]))
                result[pa[i]].insert({"VE", a.body_id, b.body_id, {ia[i]}, {ib[j], ib[jn]}});
            if (on_segment(pb[j], pa[i], pa[in]))
                result[pb[j]].insert({"EV", a.body_id, b.body_id, {ia[i], ia[in]}, {ib[j]}});
        }
    }
    work.check_size(result.size());
}
std::vector<ContactSegment2> segments(const Assembly2& assembly, std::size_t a, std::size_t b) {
    GeometryWorkScope work;
    const auto& ba = assembly.bodies[a];
    const auto& bb = assembly.bodies[b];
    const auto& pa = ba.geometry.vertices;
    const auto& pb = bb.geometry.vertices;
    const auto& ia = ba.geometry.original_vertex_ids;
    const auto& ib = bb.geometry.original_vertex_ids;
    std::vector<ContactSegment2> found;
    for (std::size_t i = 0; i < pa.size(); ++i) {
        const auto in = (i + 1) % pa.size();
        const auto e = sub(pa[in], pa[i]);
        for (std::size_t j = 0; j < pb.size(); ++j) {
            work.step();
            const auto jn = (j + 1) % pb.size();
            if (cross(e, sub(pb[jn], pb[j])) != Rational(0) || cross(e, sub(pb[j], pa[i])) != Rational(0)) continue;
            std::set<Point> ends;
            for (const auto& p : std::array<Point, 4>{pa[i], pa[in], pb[j], pb[jn]})
                if (on_segment(p, pa[i], pa[in]) && on_segment(p, pb[j], pb[jn])) ends.insert(p);
            if (ends.size() >= 2)
                found.push_back({a, b, *ends.begin(), *ends.rbegin(), e,
                    {{"EE", ba.body_id, bb.body_id, {ia[i], ia[in]}, {ib[j], ib[jn]}}}});
        }
    }
    bool changed = true;
    while (changed) {
        changed = false;
        for (std::size_t i = 0; i < found.size() && !changed; ++i) {
            for (std::size_t j = i + 1; j < found.size(); ++j) {
                work.step();
                auto& s = found[i];
                const auto& t = found[j];
                if (cross(s.tangent, t.tangent) != Rational(0) || cross(s.tangent, sub(t.start, s.start)) != Rational(0)) continue;
                if (std::max(s.start, t.start) <= std::min(s.end, t.end)) {
                    s.start = std::min(s.start, t.start);
                    s.end = std::max(s.end, t.end);
                    std::set<Source2> sources(s.sources.begin(), s.sources.end());
                    sources.insert(t.sources.begin(), t.sources.end());
                    s.sources.assign(sources.begin(), sources.end());
                    found.erase(found.begin() + static_cast<std::ptrdiff_t>(j));
                    changed = true;
                    break;
                }
            }
        }
    }
    std::sort(found.begin(), found.end(), [](const auto& s, const auto& t) { return std::tie(s.start, s.end) < std::tie(t.start, t.end); });
    return found;
}
std::vector<ExactContact2> point_constraints(const Assembly2& assembly, const ContactPoint2& point,
                                           const std::vector<ContactSegment2>& pair_segments) {
    std::vector<ExactContact2> out;
    for (const auto& n : point.boundaries) {
        const bool interior = std::any_of(pair_segments.begin(), pair_segments.end(), [&](const auto& s) {
            return point.point != s.start && point.point != s.end && on_segment(point.point, s.start, s.end)
                && cross(n, rot(s.tangent)) == Rational(0);
        });
        if (interior) continue;
        bool found = false;
        for (std::size_t side = 0; side < 2 && !found; ++side) {
            const auto& body = assembly.bodies[side == 0 ? point.a : point.b];
            const auto& poly = body.geometry.vertices;
            const auto& ids = body.geometry.original_vertex_ids;
            for (std::size_t i = 0; i < poly.size(); ++i) {
                const auto in = (i + 1) % poly.size();
                if (!on_segment(point.point, poly[i], poly[in])) continue;
                const auto tangent = mul(sub(poly[in], poly[i]), side == 0 ? 1 : -1);
                if (cross(n, rot(tangent)) == Rational(0) && dot(n, rot(tangent)) > Rational(0)) {
                    out.push_back({point.a, point.b, point.point, tangent, point.sources,
                        {assembly.bodies[point.a].body_id, assembly.bodies[point.b].body_id, point.point,
                         body.body_id, {ids[i], ids[in]}}});
                    found = true;
                    break;
                }
            }
        }
        if (!found) throw std::logic_error("free-cone boundary lacks incident directed edge");
    }
    return out;
}
Dofs free_dofs(const Assembly2& assembly) {
    GeometryWorkScope work;
    Dofs out;
    for (std::size_t i = 0; i < assembly.bodies.size(); ++i)
        for (std::size_t k = 0; k < 3; ++k)
            if (assembly.bodies[i].boundary_type != "FIXED_BODY" && assembly.bodies[i].dof_mask[k]) {
                out.push_back({i, k}); work.check_size(out.size());
            }
    return out;
}
Vector velocity_row(const Assembly2& assembly, std::size_t a, std::size_t b, const Point& p,
                    const Point& normal, const Dofs& dofs) {
    Vector result;
    for (const auto& dof : dofs) {
        const auto i = dof[0], k = dof[1];
        Rational value;
        if (i == a || i == b) {
            value = k < 2 ? normal[k] : cross(sub(p, assembly.bodies[i].dof_anchor), normal);
            if (i == b) value = -value;
        }
        result.push_back(value);
    }
    return result;
}
std::optional<ConeReachability2> reachable(const Assembly2& assembly,
                                         const std::vector<ExactContact2>& constraints,
                                         const ContactPoint2& point) {
    GeometryWorkScope work;
    auto [H, dofs] = constraint_matrix(assembly, constraints);
    if (point.forbidden.size() != 1 || point.forbidden[0].empty()) return std::nullopt;
    Vector rhs(H.size(), Rational(0));
    for (const auto& n : point.forbidden[0]) {
        H.push_back(velocity_row(assembly, point.a, point.b, point.point, n, dofs));
        rhs.push_back(Rational(1));
    }
    check_matrix_size(work, dofs.size() + 1, H.size());
    Matrix A(dofs.size(), Vector(H.size()));
    for (std::size_t k = 0; k < dofs.size(); ++k)
        for (std::size_t i = 0; i < H.size(); ++i) A[k][i] = H[i][k];
    A.push_back(rhs);
    Vector b(dofs.size(), Rational(0));
    b.push_back(Rational(1));
    const auto cert = opt::solve(A, b, Vector(H.size()));
    if (cert.status == opt::Status::optimal) {
        if (cert.exact_x.size() != H.size()) throw std::logic_error("unreachable certificate width");
        for (const auto& w : cert.exact_x) if (w < Rational(0)) throw std::logic_error("negative Farkas weight");
        for (std::size_t i = 0; i < A.size(); ++i)
            if (vdot(A[i], cert.exact_x) != b[i]) throw std::logic_error("unreachable-cone exact verification failed");
        return ConeReachability2{point, dofs, H, rhs, true, cert.exact_x, std::nullopt};
    }
    if (cert.status != opt::Status::infeasible) return std::nullopt;
    const auto size = dofs.size();
    check_matrix_size(work, H.size(), 2 * size + H.size());
    A.assign(H.size(), Vector(2 * size + H.size()));
    for (std::size_t i = 0; i < H.size(); ++i) {
        for (std::size_t k = 0; k < size; ++k) { A[i][k] = H[i][k]; A[i][size + k] = -H[i][k]; }
        A[i][2 * size + i] = Rational(-1);
    }
    const auto witness = opt::solve(A, rhs, Vector(2 * size + H.size()));
    if (witness.status != opt::Status::optimal) return std::nullopt;
    Vector v(size);
    for (std::size_t k = 0; k < size; ++k) v[k] = witness.exact_x[k] - witness.exact_x[size + k];
    for (std::size_t i = 0; i < H.size(); ++i)
        if (vdot(H[i], v) < rhs[i]) throw std::logic_error("reachable-cone exact verification failed");
    return ConeReachability2{point, dofs, H, rhs, false, std::nullopt, v};
}
void validate_assembly(const Assembly2& assembly) {
    if (assembly.bodies.empty()) throw std::invalid_argument("assembly needs bodies");
    if (assembly.profile != "profile1") throw std::invalid_argument("unsupported profile");
    if (assembly.completeness != "complete" && assembly.completeness != "completeness_unknown")
        throw std::invalid_argument("unknown completeness");
    std::set<std::string> names;
    for (const auto& body : assembly.bodies) {
        if (body.body_id.empty() || !names.insert(body.body_id).second) throw std::invalid_argument("body IDs must be unique nonempty strings");
        if (body.boundary_type != "" && body.boundary_type != "FIXED_BODY" && body.boundary_type != "FORCE_CONTROLLED_PLATE")
            throw std::invalid_argument("unknown boundary_type");
        for (const int bit : body.dof_mask) if (bit != 0 && bit != 1) throw std::invalid_argument("dof_mask must contain binary values");
        if (body.boundary_type == "FIXED_BODY" && body.dof_mask != std::array<int, 3>{0, 0, 0})
            throw std::invalid_argument("fixed body needs explicit zero mask");
    }
    if (!assembly.pairs) {
        if (assembly.completeness == "complete") throw std::invalid_argument("complete assembly requires explicit candidate pairs");
        return;
    }
    std::set<std::array<std::size_t, 2>> canonical;
    for (auto pair : *assembly.pairs) {
        if (pair[0] == pair[1] || pair[0] >= assembly.bodies.size() || pair[1] >= assembly.bodies.size())
            throw std::invalid_argument("invalid candidate pair");
        if (pair[0] > pair[1]) std::swap(pair[0], pair[1]);
        canonical.insert(pair);
    }
    if (assembly.completeness == "complete" && canonical.size() != assembly.bodies.size() * (assembly.bodies.size() - 1) / 2)
        throw std::invalid_argument("complete candidate list must include all pairs");
}
} // namespace

Body2::Body2(std::string id, geometry2::Body shape, Point reference, std::string boundary,
             std::array<int, 3> mask, std::optional<Point> anchor)
    : body_id(std::move(id)), geometry(std::move(shape)), reference_point(std::move(reference)),
      boundary_type(std::move(boundary)), dof_mask(mask), dof_anchor(anchor ? *anchor : reference_point) {
    if (body_id.empty()) throw std::invalid_argument("body ID must be a nonempty string");
    if (boundary_type != "" && boundary_type != "FIXED_BODY" && boundary_type != "FORCE_CONTROLLED_PLATE")
        throw std::invalid_argument("unknown boundary_type");
    for (const int bit : mask) if (bit != 0 && bit != 1) throw std::invalid_argument("dof_mask must contain binary values");
    if (boundary_type == "FIXED_BODY" && mask != std::array<int, 3>{0, 0, 0})
        throw std::invalid_argument("fixed body needs explicit zero mask");
    if (!anchor && (boundary_type == "FORCE_CONTROLLED_PLATE" ||
        (boundary_type != "FIXED_BODY" && mask != std::array<int, 3>{1, 1, 1})))
        throw std::invalid_argument("partly constrained body needs explicit dof_anchor");
}
bool Source2::operator<(const Source2& other) const {
    return std::tie(kind, a, feature_a, b, feature_b) < std::tie(other.kind, other.a, other.feature_a, other.b, other.feature_b);
}
Point ExactContact2::normal() const { return rot(tangent); }

std::pair<Matrix, Dofs> constraint_matrix(const Assembly2& assembly, const std::vector<ExactContact2>& constraints) {
    GeometryWorkScope work;
    Dofs dofs = free_dofs(assembly);
    check_matrix_size(work, constraints.size(), dofs.size());
    Matrix rows;
    for (const auto& c : constraints) rows.push_back(velocity_row(assembly, c.a, c.b, c.point, c.normal(), dofs));
    return {rows, dofs};
}

ContactSet2 assemble_contact_set2(const Assembly2& assembly) {
    GeometryWorkScope work(assembly.limits);
    exact::IntegerLimitScope integers(assembly.limits.max_integer_bits);
    work.check_size(assembly.bodies.size());
    validate_assembly(assembly);
    ContactSet2 result;
    result.assembly = assembly;
    result.completeness = assembly.completeness;
    std::vector<std::array<std::size_t, 2>> pairs;
    if (assembly.pairs) pairs = *assembly.pairs;
    else {
        const auto count = assembly.bodies.size();
        if (count > 1) {
            const auto first = count % 2 == 0 ? count / 2 : count;
            const auto second = count % 2 == 0 ? count - 1 : (count - 1) / 2;
            if (first > work.limits.max_elements / second)
                throw exact::ResourceLimit("L1 candidate pair element limit exceeded");
        }
        for (std::size_t a = 0; a < count; ++a)
            for (std::size_t b = a + 1; b < count; ++b) pairs.push_back({a, b});
    }
    work.check_size(pairs.size());
    std::set<std::array<std::size_t, 2>> original(pairs.begin(), pairs.end()), canonical;
    for (auto pair : original) { if (pair[0] > pair[1]) std::swap(pair[0], pair[1]); canonical.insert(pair); }
    std::set<Source2> raw;
    for (const auto& pair : canonical) {
        work.step();
        const auto a = pair[0], b = pair[1];
        const auto& ba = assembly.bodies[a];
        const auto& bb = assembly.bodies[b];
        const int state = geometry2::polygons_overlap_exact(ba.geometry, bb.geometry, {0, 0});
        result.pair_states.push_back({static_cast<int>(a), static_cast<int>(b), state});
        if (state == 1) {
            ContactSet2 rejected;
            rejected.assembly = assembly;
            rejected.completeness = assembly.completeness;
            rejected.mathematical_status = "OVERLAP";
            rejected.reason = "overlap_initial_state";
            rejected.pair_states = result.pair_states;
            return rejected;
        }
        if (state == -1) continue;
        PointSources sources;
        for (const auto& ordered : original)
            if (std::min(ordered[0], ordered[1]) == a && std::max(ordered[0], ordered[1]) == b)
                raw_pair(sources, assembly.bodies[ordered[0]], assembly.bodies[ordered[1]]);
        const auto pair_segments = segments(assembly, a, b);
        result.segments.insert(result.segments.end(), pair_segments.begin(), pair_segments.end());
        work.check_size(result.segments.size());
        for (const auto& entry : sources) {
            work.step();
            ContactPoint2 point{a, b, entry.first, {}, {}, {entry.second.begin(), entry.second.end()}, {}, false};
            raw.insert(entry.second.begin(), entry.second.end());
            work.check_size(raw.size());
            point_cone(point, ba.geometry.vertices, bb.geometry.vertices);
            if (point.fp_type == "CONVEX") {
                const auto kept = point_constraints(assembly, point, pair_segments);
                result.constraints.insert(result.constraints.end(), kept.begin(), kept.end());
                point.retained = !kept.empty();
            }
            result.points.push_back(std::move(point));
            work.check_size(result.points.size());
            work.check_size(result.constraints.size());
        }
    }
    result.raw_sources.assign(raw.begin(), raw.end());
    for (auto& point : result.points) {
        if (point.fp_type == "CONVEX") continue;
        const auto proof = reachable(assembly, result.constraints, point);
        if (proof && proof->unreachable) {
            result.redundancy_certificates.push_back(*proof);
            point.fp_type = "REDUNDANT_PROVED";
        } else {
            result.unresolved.push_back(point);
            if (proof) result.reachable_witnesses.push_back(*proof);
        }
    }
    result.status = result.unresolved.empty() ? "RESOLVED" : "MECHANICAL_UNRESOLVED";
    result.mathematical_status = *result.status;
    if (!result.unresolved.empty()) result.reason = "reachable_or_unproved_open_cone";
    return result;
}

LockCertificate query_lock(const geometry2::Body& moving, const std::vector<geometry2::Body>& fixed,
                           const geometry2::GeometryLimits& limits) {
    GeometryWorkScope work(limits);
    exact::IntegerLimitScope integers(limits.max_integer_bits);
    work.check_size(fixed.size());
    std::vector<geometry2::Entrance> pairs;
    LockCertificate out;
    for (const auto& body : fixed) {
        // Lock certificates preserve the referee's original ear-product cells.
        // Convex merging preserves E/O but changes cell witnesses and r bounds.
        pairs.emplace_back(moving, body, false, true, limits);
        out.pair_states.push_back(pairs.back().membership({0, 0}));
    }
    if (std::find(out.pair_states.begin(), out.pair_states.end(), 1) != out.pair_states.end()) {
        out.reason = "overlap_initial_state";
        out.mathematical_status = "OVERLAP";
        out.display_status = "NOT_APPLICABLE";
        return out;
    }
    std::optional<Rational> minimum;
    for (std::size_t ni = 0; ni < pairs.size(); ++ni) {
        const auto& pair = pairs[ni];
        const auto local = geometry2::local_origin(pair);
        for (const auto& cell : local.cells)
            out.local_cells.push_back({ni, cell.cell_index, cell.piece_a, cell.piece_b, cell.vertices, cell.active_edges});
        for (const auto& bound : local.radius_bounds) {
            out.radius_bounds.push_back({ni, bound.cell_index, bound.edge_index, bound.edge[0], bound.edge[1], bound.squared_distance});
            if (!minimum || bound.squared_distance < *minimum) minimum = bound.squared_distance;
        }
        work.check_size(out.local_cells.size());
        work.check_size(out.radius_bounds.size());
        if (out.pair_states[ni] != 0) continue;
        // The Python lock referee orders VE first, then EV. These indices
        // identify normalized rings; the case exporter maps original IDs.
        const auto& pa = pair.a.vertices;
        const auto& pb = pair.b.vertices;
        for (std::size_t i = 0; i < pa.size(); ++i)
            for (std::size_t j = 0; j < pb.size(); ++j)
                if (on_segment(pa[i], pb[j], pb[(j + 1) % pb.size()])) out.contact_sources.push_back({ni, {"VE", i, j}, pa[i]});
        for (std::size_t j = 0; j < pb.size(); ++j)
            for (std::size_t i = 0; i < pa.size(); ++i)
                if (on_segment(pb[j], pa[i], pa[(i + 1) % pa.size()])) out.contact_sources.push_back({ni, {"EV", i, j}, pb[j]});
        work.check_size(out.contact_sources.size());
    }
    out.radius = minimum ? *minimum / (Rational(1) + *minimum) : Rational(1);
    std::set<Point> unique{{1, 0}, {0, 1}, {-1, 0}, {0, -1}};
    for (const auto& cell : out.local_cells)
        for (const auto& edge : cell.active_edges) { const auto r = ray(sub(edge[1], edge[0])); unique.insert(r); unique.insert(neg(r)); }
    std::vector<Point> ordered(unique.begin(), unique.end());
    std::sort(ordered.begin(), ordered.end(), angle_less);
    auto classify = [&](LockArc2& arc) {
        bool contact = false;
        for (const auto& cell : out.local_cells) {
            bool closed = true, open = true;
            for (const auto& edge : cell.active_edges) {
                work.step();
                const int sign = cross(sub(edge[1], edge[0]), arc.sample).sign();
                closed = closed && sign >= 0;
                open = open && sign > 0;
            }
            if (open) arc.blockers.push_back({cell.neighbor_index, cell.cell_index});
            else if (closed) contact = true;
        }
        arc.state = !arc.blockers.empty() ? "PENETRATING" : contact ? "CONTACT" : "SEPARATING";
    };
    for (std::size_t i = 0; i < ordered.size(); ++i) {
        const auto& start = ordered[i];
        const auto& end = ordered[(i + 1) % ordered.size()];
        LockArc2 line{"RAY", start, start, start, {}, {}};
        classify(line);
        out.arcs.push_back(std::move(line));
        auto middle = add(start, end);
        if (middle == Point{0, 0}) middle = rot(start);
        LockArc2 arc{"OPEN_ARC", start, end, ray(middle), {}, {}};
        classify(arc);
        out.arcs.push_back(std::move(arc));
    }
    std::optional<Point> separation, touching;
    for (const auto& arc : out.arcs) {
        if (!separation && arc.state == "SEPARATING") separation = arc.sample;
        if (!touching && arc.state == "CONTACT") touching = arc.sample;
    }
    if (std::find(out.pair_states.begin(), out.pair_states.end(), 0) == out.pair_states.end()) out.status = "NOT_CONTACT";
    else if (separation) { out.status = "REMOVABLE_TRANSLATION"; out.separation_ray = separation; }
    else { out.status = "NOT_SEPARABLE_TRANSLATION"; out.refinement = touching ? "SEAM_SLIDING" : "TRANSLATION_IMMOBILE"; out.seam_ray = touching; }
    out.mathematical_status = out.status;
    return out;
}

std::pair<Matrix, Matrix> double_description(const Matrix& rows, std::size_t size) {
    GeometryWorkScope work;
    check_matrix_size(work, rows.size(), size);
    check_matrix_size(work, size, size);
    for (const auto& row : rows) if (row.size() != size) throw std::invalid_argument("matrix width mismatch");
    Matrix lines(size, Vector(size)), rays, processed;
    for (std::size_t k = 0; k < size; ++k) lines[k][k] = Rational(1);
    for (const auto& row : rows) {
        std::size_t pivot = 0;
        while (pivot < lines.size() && vdot(row, lines[pivot]) == Rational(0)) ++pivot;
        if (pivot < lines.size()) {
            auto line = lines[pivot];
            auto value = vdot(row, line);
            if (value < Rational(0)) { line = vneg(line); value = -value; }
            Matrix kept, projected;
            for (std::size_t k = 0; k < lines.size(); ++k) {
                if (k == pivot) continue;
                auto old = lines[k];
                const auto ratio = vdot(row, old) / value;
                for (std::size_t j = 0; j < size; ++j) old[j] = old[j] - ratio * line[j];
                kept.push_back(std::move(old));
            }
            for (auto old : rays) {
                const auto ratio = vdot(row, old) / value;
                for (std::size_t j = 0; j < size; ++j) old[j] = old[j] - ratio * line[j];
                projected.push_back(std::move(old));
            }
            projected.push_back(std::move(line));
            lines = unique_rays(kept);
            rays = unique_rays(projected);
        } else {
            std::vector<std::pair<Vector, Rational>> positive, negative;
            Matrix kept;
            for (const auto& r : rays) {
                const auto value = vdot(row, r);
                if (value > Rational(0)) positive.push_back({r, value});
                else if (value < Rational(0)) negative.push_back({r, value});
                else kept.push_back(r);
            }
            for (const auto& a : positive) {
                kept.push_back(a.first);
                for (const auto& b : negative) {
                    work.step();
                    Matrix common;
                    for (const auto& old : processed)
                        if (vdot(old, a.first) == Rational(0) && vdot(old, b.first) == Rational(0)) common.push_back(old);
                    // Signed arithmetic is essential in dimension zero/one.
                    if (static_cast<std::ptrdiff_t>(rank(common, size)) >= static_cast<std::ptrdiff_t>(size) - static_cast<std::ptrdiff_t>(lines.size()) - 2) {
                        Vector v(size);
                        for (std::size_t j = 0; j < size; ++j) v[j] = a.second * b.first[j] - b.second * a.first[j];
                        kept.push_back(std::move(v));
                    }
                }
            }
            rays = unique_rays(kept);
        }
        work.check_size(rays.size());
        processed.push_back(row);
    }
    for (const auto& row : rows) {
        for (const auto& r : rays) if (vdot(row, r) < Rational(0)) throw std::logic_error("ray failed exact feasibility");
        for (const auto& l : lines) if (vdot(row, l) != Rational(0)) throw std::logic_error("free line failed exact feasibility");
    }
    if (rank(lines, size) != size - rank(rows, size)) throw std::logic_error("free line basis has incorrect rank");
    return {rays, lines};
}

FirstOrderResult2 first_order_mobility(const ContactSet2& contacts) {
    GeometryWorkScope work(contacts.assembly.limits);
    exact::IntegerLimitScope integers(contacts.assembly.limits.max_integer_bits);
    FirstOrderResult2 out;
    out.dofs = free_dofs(contacts.assembly);
    if (contacts.call_status != "OK") { out.call_status = contacts.call_status; out.reason = contacts.reason; return out; }
    if (contacts.status == "MECHANICAL_UNRESOLVED" || !contacts.unresolved.empty()) {
        out.mathematical_status = "MECHANICAL_UNRESOLVED"; out.reason = "contact_set_unresolved"; return out;
    }
    if (contacts.status != "RESOLVED") { out.mathematical_status = contacts.mathematical_status; out.reason = contacts.reason; return out; }
    if (contacts.completeness != "complete") { out.mathematical_status = "UNPROVED"; out.reason = "completeness_unknown"; return out; }
    auto [rows, dofs] = constraint_matrix(contacts.assembly, contacts.constraints);
    out.dofs = std::move(dofs);
    out.matrix = rows;
    const auto size = out.dofs.size(), count = rows.size(), width = 2 * size + count + 1;
    check_matrix_size(work, count + 1, width);
    out.exact_rank = rank(rows, size);
    NormalizedConeLP2 proof;
    proof.matrix.assign(count + 1, Vector(width));
    proof.rhs.assign(count + 1, Rational(0));
    proof.rhs.back() = Rational(1);
    proof.objective.assign(width, Rational(0));
    for (std::size_t i = 0; i < count; ++i) {
        for (std::size_t k = 0; k < size; ++k) { proof.matrix[i][k] = rows[i][k]; proof.matrix[i][size + k] = -rows[i][k]; }
        proof.matrix[i][2 * size + i] = Rational(-1);
        proof.objective[2 * size + i] = Rational(1);
    }
    for (std::size_t k = 2 * size; k < width; ++k) proof.matrix.back()[k] = Rational(1);
    const auto result = opt::maximize(proof.matrix, proof.rhs, proof.objective);
    if (result.status != opt::Status::optimal) throw std::logic_error("normalized cone LP lacks exact optimum");
    proof.exact_x = result.exact_x;
    proof.exact_y = result.exact_y;
    const auto value = vdot(proof.objective, proof.exact_x);
    if ((value != Rational(0) && value != Rational(1)) || vdot(proof.rhs, proof.exact_y) != value)
        throw std::logic_error("normalized cone objective certificate failed");
    for (const auto& x : proof.exact_x) if (x < Rational(0)) throw std::logic_error("normalized cone primal nonnegativity failed");
    for (std::size_t i = 0; i < proof.matrix.size(); ++i)
        if (vdot(proof.matrix[i], proof.exact_x) != proof.rhs[i]) throw std::logic_error("normalized cone primal equation failed");
    for (std::size_t j = 0; j < width; ++j) {
        Rational dual;
        for (std::size_t i = 0; i < proof.matrix.size(); ++i) dual = dual + proof.matrix[i][j] * proof.exact_y[i];
        if (dual < proof.objective[j]) throw std::logic_error("normalized cone dual inequality failed");
    }
    auto [rays, lines] = double_description(rows, size);
    const bool zero = *out.exact_rank == size && value == Rational(0);
    if (zero != (rays.empty() && lines.empty())) throw std::logic_error("DD and normalized rank test disagree");
    std::vector<ZeroConeCombination2> combinations;
    if (zero) {
        Matrix A(size, Vector(count));
        for (std::size_t k = 0; k < size; ++k) for (std::size_t i = 0; i < count; ++i) A[k][i] = rows[i][k];
        for (std::size_t coordinate = 0; coordinate < size; ++coordinate) {
            for (const int sign : {-1, 1}) {
                Vector target(size);
                target[coordinate] = Rational(sign);
                const auto cert = opt::maximize(A, target, Vector(count));
                if (cert.status != opt::Status::optimal) throw std::logic_error("zero cone combination unavailable");
                for (const auto& w : cert.exact_x) if (w < Rational(0)) throw std::logic_error("negative zero cone multiplier");
                for (std::size_t k = 0; k < size; ++k)
                    if (vdot(A[k], cert.exact_x) != target[k]) throw std::logic_error("zero cone combination failed verification");
                combinations.push_back({coordinate, sign, cert.exact_x});
            }
        }
    }
    Matrix generators = rays;
    for (const auto& line : lines) { generators.push_back(line); generators.push_back(vneg(line)); }
    out.mathematical_status = zero ? "ZERO_CONE" : "NONZERO_CONE";
    out.cone_is_zero = zero;
    out.display_status = "EXACT";
    out.normalized_value = value;
    out.normalization_certificate = std::move(proof);
    out.rays = std::move(rays);
    out.lineality = std::move(lines);
    out.generators = unique_rays(generators);
    out.zero_certificates = std::move(combinations);
    return out;
}
FirstOrderResult2 first_order_mobility(const Assembly2& assembly) { return first_order_mobility(assemble_contact_set2(assembly)); }

namespace {
std::string quoted(const std::string& text) {
    static const char hex[] = "0123456789abcdef";
    std::string out = "\"";
    for (const unsigned char c : text) {
        if (c == '\\' || c == '"') { out += '\\'; out += static_cast<char>(c); }
        else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
        else out += static_cast<char>(c);
    }
    return out + '"';
}
std::string js(const Rational& value) { return quoted(value.canonical()); }
std::string js(const Point& value) { return geometry2::point_json(value); }
std::string js(const std::string& value) { return quoted(value); }
std::string js(bool value) { return value ? "true" : "false"; }
std::string js(int value) { return std::to_string(value); }
std::string js(std::size_t value) { return std::to_string(value); }
template <class Range, class Function> std::string array_json(const Range& range, Function function) {
    std::string out = "[";
    bool first = true;
    for (const auto& value : range) { if (!first) out += ','; first = false; out += function(value); }
    return out + ']';
}
template <class T> std::string optional_json(const std::optional<T>& value) { return value ? js(*value) : "null"; }
std::string vector_json(const Vector& values) { return array_json(values, [](const auto& x) { return js(x); }); }
std::string matrix_json(const Matrix& values) { return array_json(values, [](const auto& x) { return vector_json(x); }); }
std::string points_json(const std::vector<Point>& values) { return array_json(values, [](const auto& x) { return js(x); }); }
template <class T, std::size_t N> std::string ints_json(const std::array<T, N>& values) {
    return array_json(values, [](auto x) { return std::to_string(x); });
}
std::string dofs_json(const Dofs& values) { return array_json(values, [](const auto& x) { return ints_json(x); }); }
std::string source_json(const Source2& source) {
    auto feature = [](const auto& ids) {
        return ids.size() == 1 ? std::to_string(ids[0]) : array_json(ids, [](auto id) { return std::to_string(id); });
    };
    return '[' + quoted(source.kind) + ',' + quoted(source.a) + ',' + feature(source.feature_a) + ',' +
        quoted(source.b) + ',' + feature(source.feature_b) + ']';
}
std::string sources_json(const std::vector<Source2>& sources) { return array_json(sources, source_json); }
std::string point_record_json(const ContactPoint2& p) {
    return "{\"a\":" + js(p.a) + ",\"b\":" + js(p.b) + ",\"point\":" + js(p.point) +
        ",\"fp_type\":" + quoted(p.fp_type) + ",\"boundaries\":" + points_json(p.boundaries) +
        ",\"sources\":" + sources_json(p.sources) + ",\"forbidden\":" +
        array_json(p.forbidden, [](const auto& cone) { return points_json(cone); }) + ",\"retained\":" + js(p.retained) + '}';
}
std::string reachability_json(const ConeReachability2& c) {
    return "{\"point\":" + point_record_json(c.point) + ",\"dofs\":" + dofs_json(c.dofs) +
        ",\"matrix\":" + matrix_json(c.matrix) + ",\"rhs\":" + vector_json(c.rhs) +
        ",\"unreachable\":" + js(c.unreachable) + ",\"multipliers\":" +
        (c.multipliers ? vector_json(*c.multipliers) : "null") + ",\"twist\":" +
        (c.twist ? vector_json(*c.twist) : "null") + '}';
}
std::string normalized_json(const NormalizedConeLP2& p) {
    return "{\"matrix\":" + matrix_json(p.matrix) + ",\"rhs\":" + vector_json(p.rhs) +
        ",\"objective\":" + vector_json(p.objective) + ",\"exact_x\":" + vector_json(p.exact_x) +
        ",\"exact_y\":" + vector_json(p.exact_y) + '}';
}
} // namespace

std::string export_exact(const ContactSet2& result) {
    std::ostringstream out;
    out << "{\"status\":" << optional_json(result.status) << ",\"call_status\":" << quoted(result.call_status)
        << ",\"mathematical_status\":" << quoted(result.mathematical_status) << ",\"completeness\":" << quoted(result.completeness)
        << ",\"reason\":" << optional_json(result.reason) << ",\"constraints\":";
    out << array_json(result.constraints, [](const ExactContact2& c) {
        const auto& l = c.label;
        return "{\"a\":" + js(c.a) + ",\"b\":" + js(c.b) + ",\"point\":" + js(c.point) +
            ",\"tangent\":" + js(c.tangent) + ",\"sources\":" + sources_json(c.sources) +
            ",\"label\":[" + quoted(l.a) + ',' + quoted(l.b) + ',' + js(l.point) + ',' + quoted(l.edge_body) + ',' + ints_json(l.edge) + "]}";
    });
    out << ",\"points\":" << array_json(result.points, point_record_json)
        << ",\"raw_sources\":" << sources_json(result.raw_sources)
        << ",\"unresolved\":" << array_json(result.unresolved, point_record_json)
        << ",\"redundancy_certificates\":" << array_json(result.redundancy_certificates, reachability_json)
        << ",\"reachable_witnesses\":" << array_json(result.reachable_witnesses, reachability_json)
        << ",\"pair_states\":" << array_json(result.pair_states, [](const auto& p) { return ints_json(p); })
        << ",\"segments\":" << array_json(result.segments, [](const ContactSegment2& s) {
            return "{\"a\":" + js(s.a) + ",\"b\":" + js(s.b) + ",\"start\":" + js(s.start) +
                ",\"end\":" + js(s.end) + ",\"tangent\":" + js(s.tangent) + ",\"sources\":" + sources_json(s.sources) + '}';
        }) << '}';
    return out.str();
}

std::string export_exact(const LockCertificate& result) {
    std::ostringstream out;
    out << "{\"status\":" << optional_json(result.status) << ",\"refinement\":" << optional_json(result.refinement)
        << ",\"reason\":" << optional_json(result.reason) << ",\"call_status\":" << quoted(result.call_status)
        << ",\"mathematical_status\":" << optional_json(result.mathematical_status)
        << ",\"display_status\":" << quoted(result.display_status) << ",\"radius\":" << optional_json(result.radius)
        << ",\"separation_ray\":" << optional_json(result.separation_ray) << ",\"seam_ray\":" << optional_json(result.seam_ray)
        << ",\"pair_states\":" << array_json(result.pair_states, [](auto state) { return std::to_string(state); })
        << ",\"local_cells\":" << array_json(result.local_cells, [](const LocalCell2& c) {
            return "{\"neighbor_index\":" + js(c.neighbor_index) + ",\"cell_index\":" + js(c.cell_index) +
                ",\"piece_a\":" + js(c.piece_a) + ",\"piece_b\":" + js(c.piece_b) + ",\"vertices\":" + geometry2::polygon_json(c.vertices) +
                ",\"active_edges\":" + array_json(c.active_edges, [](const Segment& e) { return '[' + js(e[0]) + ',' + js(e[1]) + ']'; }) + '}';
        }) << ",\"radius_bounds\":" << array_json(result.radius_bounds, [](const RadiusBound2& b) {
            return "{\"neighbor_index\":" + js(b.neighbor_index) + ",\"cell_index\":" + js(b.cell_index) +
                ",\"edge_index\":" + js(b.edge_index) + ",\"start\":" + js(b.start) + ",\"end\":" + js(b.end) +
                ",\"squared_distance\":" + js(b.squared_distance) + '}';
        }) << ",\"arcs\":" << array_json(result.arcs, [](const LockArc2& a) {
            return "{\"kind\":" + quoted(a.kind) + ",\"start\":" + js(a.start) + ",\"end\":" + js(a.end) +
                ",\"sample\":" + js(a.sample) + ",\"state\":" + quoted(a.state) + ",\"blockers\":" +
                array_json(a.blockers, [](const auto& b) { return ints_json(b); }) + '}';
        }) << ",\"contact_sources\":" << array_json(result.contact_sources, [](const ContactSource2& s) {
            return "{\"neighbor_index\":" + js(s.neighbor_index) + ",\"label\":" + geometry2::label_json(s.label) + ",\"point\":" + js(s.point) + '}';
        }) << '}';
    return out.str();
}

std::string export_exact(const FirstOrderResult2& result) {
    std::ostringstream out;
    out << "{\"call_status\":" << quoted(result.call_status) << ",\"mathematical_status\":" << optional_json(result.mathematical_status)
        << ",\"cone_is_zero\":" << optional_json(result.cone_is_zero) << ",\"display_status\":" << quoted(result.display_status)
        << ",\"dofs\":" << dofs_json(result.dofs) << ",\"matrix\":" << (result.matrix ? matrix_json(*result.matrix) : "null")
        << ",\"exact_rank\":" << optional_json(result.exact_rank) << ",\"normalized_value\":" << optional_json(result.normalized_value)
        << ",\"normalization_certificate\":" << (result.normalization_certificate ? normalized_json(*result.normalization_certificate) : "null")
        << ",\"rays\":" << (result.rays ? matrix_json(*result.rays) : "null")
        << ",\"lineality\":" << (result.lineality ? matrix_json(*result.lineality) : "null")
        << ",\"generators\":" << (result.generators ? matrix_json(*result.generators) : "null")
        << ",\"zero_certificates\":";
    if (!result.zero_certificates) out << "null";
    else out << array_json(*result.zero_certificates, [](const ZeroConeCombination2& p) {
        return "{\"coordinate\":" + js(p.coordinate) + ",\"sign\":" + js(p.sign) + ",\"multipliers\":" + vector_json(p.multipliers) + '}';
    });
    out << ",\"reason\":" << optional_json(result.reason)
        << ",\"interpretation\":\"锥 = {0} 推出不可动；锥非零推不出可动\"}";
    return out.str();
}

} // namespace eab2::contact
