#include "geometry2.hpp"
#include <algorithm>
#include <iomanip>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <tuple>

#if defined(__AVX__) || defined(__AVX2__)
#error Unsupported AVX compilation target
#endif
#if defined(_M_FP_FAST) || defined(__FAST_MATH__) || defined(_M_FP_CONTRACT)
#error Unsupported floating-point compilation mode
#endif
#pragma fp_contract(off)

namespace eab2::geometry2 {
thread_local GeometryWorkScope::State* GeometryWorkScope::active_ = nullptr;
GeometryWorkScope::GeometryWorkScope() : GeometryWorkScope(active_ ? active_->options : GeometryLimits{}) {}
GeometryWorkScope::GeometryWorkScope(const GeometryLimits& value)
    : owned_{0, value.max_work_units, value}, previous_(active_), shared_(active_ ? active_ : &owned_),
      start_(shared_->used), previous_limit_(shared_->limit), limits(value) {
    if (!limits.max_work_units || !limits.max_elements || !limits.max_integer_bits)
        throw std::invalid_argument("geometry limits must be positive");
    const auto capacity = limits.max_work_units > UINT64_MAX - shared_->used ? UINT64_MAX : shared_->used + limits.max_work_units;
    shared_->limit = std::min(shared_->limit, capacity);
    active_ = shared_;
}
GeometryWorkScope::~GeometryWorkScope() { shared_->limit = previous_limit_; active_ = previous_; }
void GeometryWorkScope::step(std::uint64_t count) {
    if (count > shared_->limit - shared_->used) throw numeric::Error(5, "geometry exact work limit exceeded");
    shared_->used += count;
}
void GeometryWorkScope::check_size(std::size_t count) const {
    if (count > limits.max_elements) throw numeric::Error(5, "geometry element limit exceeded");
}
std::uint64_t GeometryWorkScope::consumed() const { return shared_->used - start_; }
class Entrance::CacheTransaction {
    const Entrance& owner_;
    bool raw_present_, skeleton_present_, subdivision_present_, clipped_present_, committed_ = false;
    Statistics statistics_;
public:
    explicit CacheTransaction(const Entrance& owner)
        : owner_(owner), raw_present_(!owner.raw_.empty()), skeleton_present_(owner.skeleton_ready_),
          subdivision_present_(owner.subdivision_ready_), clipped_present_(owner.clipped_ready_), statistics_(owner.statistics_) {}
    ~CacheTransaction() {
        if (committed_) return;
        if (!raw_present_) owner_.raw_.clear();
        if (!skeleton_present_) { owner_.contacts_.clear(); owner_.points_.clear(); owner_.boundary_.clear(); owner_.skeleton_ready_ = false; }
        if (!subdivision_present_) { owner_.subdivision_ = {}; owner_.subdivision_ready_ = false; }
        if (!clipped_present_) { owner_.clipped_.clear(); owner_.clipped_ready_ = false; }
        owner_.statistics_ = statistics_;
    }
    void commit() { committed_ = true; }
};
namespace {
using Work = GeometryWorkScope;
void check_point_bits(const Point& point, const GeometryLimits& limits) {
    for (const auto& x : point) if (x.numerator().bit_length() > limits.max_integer_bits || x.denominator().bit_length() > limits.max_integer_bits)
        throw numeric::Error(5, "geometry integer bit limit exceeded");
}
Point middle(const Point& a, const Point& b) { return mul(add(a, b), Rational(Int(1), Int(2))); }
Point edge_vector(const Polygon& polygon, std::size_t i) { return sub(polygon[(i + 1) % polygon.size()], polygon[i]); }
Segment sorted_segment(const Point& a, const Point& b) { return b < a ? Segment{b, a} : Segment{a, b}; }
int half(const Point& v) { return v[1] > Rational(0) || (v[1] == Rational(0) && v[0] > Rational(0)) ? 0 : 1; }
bool angle_less(const Point& a, const Point& b) {
    const auto ha = half(a), hb = half(b);
    return ha != hb ? ha < hb : cross(a, b) > Rational(0);
}
std::vector<Rational> cuts(const Point& a, const Point& b, const Point& c, const Point& d) {
    const auto u = sub(b, a), v = sub(d, c), w = sub(c, a);
    const auto det = cross(u, v);
    if (det.sign()) {
        const auto s = cross(w, v) / det, t = cross(w, u) / det;
        if (s >= Rational(0) && s <= Rational(1) && t >= Rational(0) && t <= Rational(1)) return {s};
        return {};
    }
    if (cross(w, u).sign()) return {};
    const auto k = u[0].sign() ? 0 : 1;
    std::vector<Rational> out;
    for (const auto& p : {c, d}) if (on_segment(p, a, b)) out.push_back((p[k] - a[k]) / u[k]);
    return out;
}
Polygon hull(Polygon points) {
    std::sort(points.begin(), points.end());
    points.erase(std::unique(points.begin(), points.end()), points.end());
    if (points.size() <= 2) return points;
    const auto append = [](Polygon& out, const Point& p) {
        while (out.size() > 1 && cross(sub(out.back(), out[out.size() - 2]), sub(p, out.back())) <= Rational(0)) out.pop_back();
        out.push_back(p);
    };
    Polygon lo, hi;
    for (const auto& p : points) append(lo, p);
    for (auto i = points.rbegin(); i != points.rend(); ++i) append(hi, *i);
    lo.pop_back(); hi.pop_back(); lo.insert(lo.end(), hi.begin(), hi.end());
    return lo;
}
std::vector<Polygon> triangulate(const Polygon& p, Work& work) {
    std::vector<std::size_t> ids(p.size());
    std::iota(ids.begin(), ids.end(), 0);
    std::vector<Polygon> out;
    while (ids.size() > 3) {
        bool removed = false;
        for (std::size_t k = 0; k < ids.size(); ++k) {
            work.step();
            const auto h = ids[(k + ids.size() - 1) % ids.size()], i = ids[k], j = ids[(k + 1) % ids.size()];
            const auto turn = cross(sub(p[i], p[h]), sub(p[j], p[i]));
            if (turn < Rational(0)) continue;
            if (!turn.sign()) {
                ids.erase(ids.begin() + static_cast<std::ptrdiff_t>(k)); removed = true; break;
            }
            const Polygon triangle{p[h], p[i], p[j]};
            bool blocked = false;
            for (const auto m : ids) {
                work.step();
                if (m != h && m != i && m != j && cell_state(triangle, p[m]) >= 0) { blocked = true; break; }
            }
            if (blocked) continue;
            out.push_back(triangle);
            ids.erase(ids.begin() + static_cast<std::ptrdiff_t>(k)); removed = true; break;
        }
        if (!removed) throw std::logic_error("exact ear decomposition did not find an ear");
    }
    Polygon last; for (const auto i : ids) last.push_back(p[i]);
    if (signed_area2(last) > Rational(0)) out.push_back(std::move(last));
    return out;
}
std::vector<Polygon> merge_parts(std::vector<Polygon> parts, Work& work) {
    for (;;) {
        bool merged = false;
        for (std::size_t i = 0; i < parts.size() && !merged; ++i) {
            for (std::size_t j = i + 1; j < parts.size(); ++j) {
                work.step();
                std::size_t shared = 0;
                for (const auto& p : parts[i]) if (std::find(parts[j].begin(), parts[j].end(), p) != parts[j].end()) ++shared;
                if (shared < 2) continue;
                Polygon vertices = parts[i]; vertices.insert(vertices.end(), parts[j].begin(), parts[j].end());
                auto candidate = hull(std::move(vertices));
                // The pieces have disjoint interiors by induction. Equal area
                // of their containing convex hull proves exact union equality.
                if (signed_area2(candidate) != signed_area2(parts[i]) + signed_area2(parts[j])) continue;
                parts[i] = std::move(candidate); parts.erase(parts.begin() + static_cast<std::ptrdiff_t>(j));
                merged = true; break;
            }
        }
        if (!merged) return parts;
    }
}
Int gcd(Int a, Int b) {
    a = exact::abs(a); b = exact::abs(b);
    while (b.sign()) { const auto r = a % b; a = b; b = r; }
    return a;
}
std::array<Int, 3> integer_line(const Segment& e) {
    const std::array<Rational, 3> row{e[0][1] - e[1][1], e[1][0] - e[0][0], cross(e[0], e[1])};
    Int denominator(1);
    for (const auto& v : row) denominator = denominator / gcd(denominator, v.denominator()) * v.denominator();
    std::array<Int, 3> result;
    for (std::size_t k = 0; k < 3; ++k) result[k] = row[k].numerator() * (denominator / row[k].denominator());
    return result;
}
using Arrangement = std::map<Segment, std::set<std::size_t>>;
Arrangement arrange(const std::vector<Segment>& segments, Work& work, std::size_t* intersection_count = nullptr) {
    struct Row { numeric::Aabb2 box; std::array<Int, 3> line; std::size_t source; std::set<Point> points; };
    work.check_size(segments.size());
    std::vector<Row> rows;
    for (std::size_t i = 0; i < segments.size(); ++i) {
        if (segments[i][0] == segments[i][1]) throw std::logic_error("zero arrangement segment");
        rows.push_back({numeric::exact_aabb2({segments[i][0], segments[i][1]}), integer_line(segments[i]), i,
                        {segments[i][0], segments[i][1]}});
    }
    std::sort(rows.begin(), rows.end(), [](const Row& a, const Row& b) { return a.box.min_x < b.box.min_x; });
    std::set<Point> intersections;
    for (std::size_t i = 0; i < rows.size(); ++i) {
        for (std::size_t j = i + 1; j < rows.size(); ++j) {
            work.step();
            auto& a = rows[i]; auto& b = rows[j];
            if (b.box.min_x > a.box.max_x) break;
            if (!a.box.overlaps(b.box)) continue;
            const auto& al = a.line; const auto& bl = b.line;
            const auto determinant = al[0] * bl[1] - al[1] * bl[0];
            if (determinant.sign()) {
                const Point p{Rational(al[1] * bl[2] - al[2] * bl[1], determinant),
                              Rational(al[2] * bl[0] - al[0] * bl[2], determinant)};
                if (a.box.contains(p) && b.box.contains(p)) {
                    a.points.insert(p); b.points.insert(p); intersections.insert(p);
                }
            } else if (!(al[0] * bl[2] - al[2] * bl[0]).sign() && !(al[1] * bl[2] - al[2] * bl[1]).sign()) {
                for (const auto& p : {segments[a.source][0], segments[a.source][1], segments[b.source][0], segments[b.source][1]}) {
                    if (a.box.contains(p) && b.box.contains(p)) { a.points.insert(p); b.points.insert(p); intersections.insert(p); }
                }
            }
        }
    }
    Arrangement result;
    for (const auto& row : rows) {
        auto first = row.points.begin(), second = first;
        for (++second; second != row.points.end(); ++first, ++second) {
            work.step(); result[Segment{*first, *second}].insert(row.source); work.check_size(result.size());
        }
    }
    if (intersection_count) *intersection_count = intersections.size();
    return result;
}
std::vector<Segment> keys(const Arrangement& arrangement) {
    std::vector<Segment> result; for (const auto& [segment, source] : arrangement) { (void)source; result.push_back(segment); } return result;
}
Rational y_at(const Segment& e, const Rational& x) {
    return e[0][1] + (e[1][1] - e[0][1]) * (x - e[0][0]) / (e[1][0] - e[0][0]);
}
std::pair<Point, Point> normal_cone(const Polygon& p, std::size_t i) {
    const auto before = edge_vector(p, (i + p.size() - 1) % p.size()), after = edge_vector(p, i);
    return {{before[1], -before[0]}, {after[1], -after[0]}};
}
bool open_cone(const Point& lo, const Point& hi, const Point& v) { return cross(lo, v).sign() > 0 && cross(v, hi).sign() > 0; }
Rational angle_window2(const Rational& tol, const std::optional<Rational>& cone_tol, const std::vector<Point>& vectors) {
    if (cone_tol) { const auto w = std::max(*cone_tol, Rational(0)); return w * w; }
    auto least = dot(vectors[0], vectors[0]);
    for (const auto& v : vectors) least = std::min(least, dot(v, v));
    if (!least.sign()) throw std::invalid_argument("zero edge at cover vertex");
    const auto w = std::max(tol, Rational(0));
    return w * w / least;
}
bool cross_ge_window(const Point& u, const Point& v, const Rational& w2) {
    const auto c = cross(u, v);
    return c >= Rational(0) || c * c <= w2 * dot(u, u) * dot(v, v);
}
bool bisector_positive(const Point& lo, const Point& hi, const Point& v) {
    const auto a = dot(lo, v), b = dot(hi, v);
    if (a >= Rational(0) && b >= Rational(0)) return a > Rational(0) || b > Rational(0);
    if (a <= Rational(0) && b <= Rational(0)) return false;
    const auto cmp = a * a * dot(hi, hi) - b * b * dot(lo, lo);
    return a > Rational(0) ? cmp > Rational(0) : cmp < Rational(0);
}
bool cone_accepts(const Point& lo, const Point& hi, const Point& v, const Rational& w2) {
    return cross_ge_window(lo, v, w2) && cross_ge_window(v, hi, w2) && bisector_positive(lo, hi, v);
}
bool cone_nonreflex(const Point& lo, const Point& hi, const Rational& w2) {
    const auto t = cross(lo, hi), d = dot(lo, hi);
    return (t >= Rational(0) && (t > Rational(0) || d > Rational(0)))
        || (t < Rational(0) && d > Rational(0) && t * t <= w2 * dot(lo, lo) * dot(hi, hi));
}
int ve_window_side(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j,
                   const Rational& tol, const std::optional<Rational>& cone_tol) {
    const auto strict_side = ve_side_exact(a, i, b, j);
    if (strict_side >= 0) return strict_side;
    if (tol <= Rational(0) && (!cone_tol || *cone_tol <= Rational(0))) return -1;
    const auto cone = normal_cone(a, i);
    const auto e = edge_vector(b, j);
    const Point v{-e[1], e[0]};
    const auto w2 = angle_window2(tol, cone_tol, {cone.first, cone.second, e});
    return w2 > Rational(0) && cone_nonreflex(cone.first, cone.second, w2) && cone_accepts(cone.first, cone.second, v, w2) ? 0 : -1;
}
template<class T, class F> std::string array_json(const std::vector<T>& values, F encode) {
    std::string out = "["; bool first = true;
    for (const auto& value : values) { if (!first) out += ','; first = false; out += encode(value); }
    return out + ']';
}
std::string segment_json(const Segment& e) { return '[' + point_json(e[0]) + ',' + point_json(e[1]) + ']'; }
std::string labels_json(const std::vector<Label>& labels) { return array_json(labels, [](const Label& x) { return label_json(x); }); }
std::string body_json(const Body& body) {
    auto ids = [](const std::vector<std::size_t>& values) { return array_json(values, [](std::size_t i) { return std::to_string(i); }); };
    std::string out = "{\"vertices\":" + polygon_json(body.vertices) + ",\"original_vertex_ids\":" + ids(body.original_vertex_ids)
                    + ",\"original_edge_ids\":" + ids(body.original_edge_ids) + ",\"input_bits\":[";
    bool first = true;
    for (const auto& xy : body.input_bits) {
        if (!first) out += ','; first = false;
        std::ostringstream text;
        text << "[\"" << std::hex << std::setfill('0') << std::setw(16) << xy[0] << "\",\"" << std::setw(16) << xy[1] << "\"]";
        out += text.str();
    }
    return out + "]}";
}
std::string cell_json(const Cell& cell) {
    return "{\"vertices\":" + polygon_json(cell.vertices) + ",\"sample\":" + point_json(cell.sample)
         + ",\"body_state\":" + std::to_string(cell.body_state) + ",\"topology_state\":" + std::to_string(cell.topology_state) + '}';
}
void update_bits(Statistics& stats, const Point& p) {
    for (const auto& x : p) stats.max_integer_bits = std::max({stats.max_integer_bits, x.numerator().bit_length(), x.denominator().bit_length()});
}
} // namespace

Point add(const Point& a, const Point& b) { return {a[0] + b[0], a[1] + b[1]}; }
Point sub(const Point& a, const Point& b) { return {a[0] - b[0], a[1] - b[1]}; }
Point mul(const Point& a, const Rational& value) { return {a[0] * value, a[1] * value}; }
Rational cross(const Point& a, const Point& b) { return a[0] * b[1] - a[1] * b[0]; }
Rational dot(const Point& a, const Point& b) { return a[0] * b[0] + a[1] * b[1]; }
bool on_segment(const Point& p, const Point& a, const Point& b) {
    return cross(sub(b, a), sub(p, a)) == Rational(0)
        && std::min(a[0], b[0]) <= p[0] && p[0] <= std::max(a[0], b[0])
        && std::min(a[1], b[1]) <= p[1] && p[1] <= std::max(a[1], b[1]);
}
std::vector<Segment> edges(const Polygon& p) {
    std::vector<Segment> out;
    for (std::size_t i = 0; i < p.size(); ++i) out.push_back({p[i], p[(i + 1) % p.size()]});
    return out;
}
Rational signed_area2(const Polygon& p) {
    Rational area;
    if (!p.empty()) for (const auto& e : edges(p)) area = area + cross(sub(e[0], p[0]), sub(e[1], p[0]));
    return area;
}
int cell_state(const Polygon& p, const Point& x) {
    int state = 1;
    for (const auto& e : edges(p)) {
        const auto sign = cross(sub(e[1], e[0]), sub(x, e[0])).sign();
        if (sign < 0) return -1;
        if (!sign) state = 0;
    }
    return state;
}
std::string convexity_violation(const Polygon& p) {
    if (p.size() < 3) return "fewer than 3 vertices";
    for (const auto& e : edges(p)) if (e[0] == e[1]) return "zero-length edge";
    if (signed_area2(p) <= Rational(0)) return "not counter-clockwise";
    std::size_t descents = 0;
    for (std::size_t i = 0; i < p.size(); ++i) {
        const auto previous = edge_vector(p, (i + p.size() - 1) % p.size()), next = edge_vector(p, i);
        const auto turn = cross(previous, next);
        if (turn < Rational(0)) return "reflex vertex";
        if (!turn.sign() && dot(previous, next) < Rational(0)) return "backtracking vertex";
        if (angle_less(edge_vector(p, (i + 1) % p.size()), next)) ++descents;
    }
    return descents == 1 ? "" : "edge directions wind more than once";
}
Body::Body(const Polygon& points, const GeometryLimits& limits) : vertices(points) {
    Work work(limits);
    exact::IntegerLimitScope integer_scope(limits.max_integer_bits);
    work.check_size(vertices.size());
    for (const auto& p : vertices) check_point_bits(p, limits);
    if (vertices.size() > 4096) throw numeric::Error(5, "body vertex work limit exceeded");
    if (vertices.size() < 3) throw std::invalid_argument("body requires at least three vertices");
    const auto all_edges = edges(vertices);
    for (const auto& e : all_edges) if (e[0] == e[1]) throw std::invalid_argument("zero-length body edge");
    for (std::size_t i = 0; i < all_edges.size(); ++i) {
        for (std::size_t j = i + 1; j < all_edges.size(); ++j) {
            work.step();
            if (j == i + 1 || (i == 0 && j + 1 == all_edges.size())) continue;
            const auto& e = all_edges[i]; const auto& f = all_edges[j];
            if (!cuts(e[0], e[1], f[0], f[1]).empty() || !cuts(f[0], f[1], e[0], e[1]).empty())
                throw std::invalid_argument("body ring is not simple");
        }
    }
    const auto area = signed_area2(vertices);
    if (!area.sign()) throw std::invalid_argument("body ring has zero area");
    original_vertex_ids.resize(vertices.size());
    std::iota(original_vertex_ids.begin(), original_vertex_ids.end(), 0);
    if (area.sign() < 0) { std::reverse(vertices.begin(), vertices.end()); std::reverse(original_vertex_ids.begin(), original_vertex_ids.end()); }
    original_edge_ids.resize(vertices.size());
    for (std::size_t i = 0; i < vertices.size(); ++i) {
        const auto& before = vertices[(i + vertices.size() - 1) % vertices.size()];
        const auto& current = vertices[i]; const auto& next = vertices[(i + 1) % vertices.size()];
        if (!cross(sub(current, before), sub(next, current)).sign() && !on_segment(current, before, next))
            throw std::invalid_argument("body ring has a backtracking edge");
        original_edge_ids[i] = area.sign() > 0 ? original_vertex_ids[i] : original_vertex_ids[(i + 1) % vertices.size()];
    }
}
Body Body::from_bits(const std::vector<std::array<std::uint64_t, 2>>& bits, const GeometryLimits& limits) {
    Work work(limits);
    exact::IntegerLimitScope integer_scope(limits.max_integer_bits);
    work.check_size(bits.size());
    if (bits.size() > 4096) throw numeric::Error(5, "body vertex work limit exceeded");
    Polygon points;
    for (const auto& p : bits) points.push_back({numeric::decode_binary64(p[0]), numeric::decode_binary64(p[1])});
    Body result(points, limits); result.input_bits = bits; return result;
}
bool Label::operator==(const Label& other) const { return std::tie(kind, a_index, b_index) == std::tie(other.kind, other.a_index, other.b_index); }
bool Label::operator<(const Label& other) const { return std::tie(kind, a_index, b_index) < std::tie(other.kind, other.a_index, other.b_index); }

ExactEntranceBlock entrance_block_exact(const Polygon& a, const Polygon& b) {
    for (const auto* p : {&a, &b}) { const auto why = convexity_violation(*p); if (!why.empty()) throw std::invalid_argument("not exactly convex: " + why); }
    Polygon negative; for (const auto& p : a) negative.push_back(mul(p, Rational(-1)));
    const auto lowest = [](const Polygon& p) {
        std::size_t at = 0;
        for (std::size_t i = 1; i < p.size(); ++i) if (std::tie(p[i][1], p[i][0]) < std::tie(p[at][1], p[at][0])) at = i;
        return at;
    };
    auto ca = lowest(negative), cb = lowest(b);
    const auto a0 = ca, b0 = cb;
    std::size_t ia = 0, ib = 0;
    Point v = sub(b[cb], a[ca]);
    ExactEntranceBlock result;
    while (ia < a.size() || ib < b.size()) {
        result.vertices.push_back(v); result.pairs.push_back({ca, cb});
        const auto da = edge_vector(negative, (a0 + ia) % a.size()), db = edge_vector(b, (b0 + ib) % b.size());
        Facet f;
        f.start = v;
        if (ia == a.size() || (ib < b.size() && angle_less(db, da))) {
            f.label = {"VE", ca, cb}; f.direction = db; cb = (cb + 1) % b.size(); ++ib;
        } else if (ib == b.size() || angle_less(da, db)) {
            f.label = {"EV", ca, cb}; f.direction = da; ca = (ca + 1) % a.size(); ++ia;
        } else {
            f.label = {"FF", ca, cb}; f.direction = add(da, db); ca = (ca + 1) % a.size(); cb = (cb + 1) % b.size(); ++ia; ++ib;
        }
        v = add(v, f.direction); result.facets.push_back(std::move(f));
    }
    if (v != result.vertices[0]) throw std::logic_error("exact Minkowski walk failed to close");
    return result;
}
int membership_exact(const ExactEntranceBlock& entrance, const Point& point) {
    int state = 1;
    for (const auto& facet : entrance.facets) {
        const auto sign = cross(facet.direction, sub(point, facet.start)).sign();
        if (sign < 0) return -1;
        state = std::min(state, sign);
    }
    return state;
}
int vertex_side_exact(const Polygon& p, std::size_t index, const Point& direction) {
    if (p.size() < 3 || index >= p.size()) throw std::invalid_argument("vertex side index");
    const auto before = edge_vector(p, (index + p.size() - 1) % p.size()), after = edge_vector(p, index);
    const auto turn = cross(before, after);
    if (turn < Rational(0) || (!turn.sign() && dot(before, after) <= Rational(0))) return -1;
    const auto c1 = cross(direction, before), c2 = cross(after, direction);
    if (c1 < Rational(0) || c2 < Rational(0) || (!turn.sign() && dot(direction, before) >= Rational(0))) return -1;
    return c1 > Rational(0) && c2 > Rational(0) ? 1 : 0;
}
int ve_side_exact(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j) {
    if (j >= b.size()) throw std::invalid_argument("edge side index");
    return vertex_side_exact(a, i, edge_vector(b, j));
}
int ev_side_exact(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j) { return ve_side_exact(b, j, a, i); }
std::optional<Cover> ve_cover(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j,
                            const Rational& tol, const std::optional<Rational>& cone_tol) {
    const auto side = ve_window_side(a, i, b, j, tol, cone_tol);
    if (side < 0) return std::nullopt;
    const auto e = edge_vector(b, j), delta = sub(a[i], b[j]);
    const auto squared = dot(e, e), g = -cross(e, delta), t = dot(delta, e) / squared;
    const auto projection = add(b[j], mul(e, t));
    return Cover{{"VE", i, j}, Point{e[1], -e[0]}, g * g / squared, g.sign(), t, a[i], projection, side == 1, false};
}
std::optional<Cover> ev_cover(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j,
                            const Rational& tol, const std::optional<Rational>& cone_tol) {
    auto result = ve_cover(b, j, a, i, tol, cone_tol);
    if (result) {
        result->label = {"EV", i, j}; result->normal_direction = mul(*result->normal_direction, Rational(-1));
        std::swap(result->point_a, result->point_b);
    }
    return result;
}
std::optional<Cover> vv_cover(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j,
                            const Rational& tol, const std::optional<Rational>& cone_tol) {
    if (i >= a.size() || j >= b.size()) throw std::invalid_argument("vertex cover index");
    const auto ac = normal_cone(a, i), bc = normal_cone(b, j);
    if (cross(ac.first, ac.second) <= Rational(0) || cross(bc.first, bc.second) <= Rational(0)) return std::nullopt;
    const auto alo = mul(ac.first, Rational(-1)), ahi = mul(ac.second, Rational(-1));
    const std::array<Point, 4> rays{alo, ahi, bc.first, bc.second};
    bool intersects = false;
    for (std::size_t k = 0; k < rays.size(); ++k) for (std::size_t l = k + 1; l < rays.size(); ++l) {
        const auto sum = add(rays[k], rays[l]);
        if (open_cone(alo, ahi, sum) && open_cone(bc.first, bc.second, sum)) intersects = true;
    }
    if (!intersects) return std::nullopt;
    const auto difference = sub(a[i], b[j]);
    const auto squared = dot(difference, difference);
    const bool coincident = squared == Rational(0);
    const bool active = coincident || (open_cone(alo, ahi, difference) && open_cone(bc.first, bc.second, difference));
    const auto w2 = angle_window2(tol, cone_tol, {alo, ahi, bc.first, bc.second});
    const bool expanded = !coincident && w2 > Rational(0) && cone_accepts(alo, ahi, difference, w2)
                          && cone_accepts(bc.first, bc.second, difference, w2);
    return Cover{{"VV", i, j}, coincident ? std::nullopt : std::optional<Point>(difference), squared, coincident ? 0 : 1,
                 std::nullopt, a[i], b[j], active, expanded};
}
std::vector<Cover> enumerate_covers(const Polygon& a, const Polygon& b, const std::optional<Rational>& window,
                                  bool require_in_segment, const Rational& tol, const std::optional<Rational>& cone_tol,
                                  const std::optional<Rational>& seg_tol) {
    Work work;
    work.check_size(a.size()); work.check_size(b.size());
    std::vector<Cover> result;
    if (window && *window < Rational(0)) return result;
    const auto window2 = window ? *window * *window : Rational(0);
    const auto segment_window = std::max(seg_tol ? *seg_tol : tol, Rational(0));
    const auto accept = [&](const std::optional<Cover>& cover, bool vertex) {
        if (!cover || (window && cover->gap_squared > window2)) return;
        if (vertex && !cover->strict && !cover->window_active) return;
        if (!vertex && require_in_segment) {
            const auto& polygon = cover->label.kind == "VE" ? b : a;
            const auto index = cover->label.kind == "VE" ? cover->label.b_index : cover->label.a_index;
            const auto edge = edge_vector(polygon, index);
            const auto excess = std::max({-*cover->param, *cover->param - Rational(1), Rational(0)});
            if (excess * excess * dot(edge, edge) > segment_window * segment_window) return;
        }
        result.push_back(*cover);
        work.check_size(result.size());
    };
    for (std::size_t i = 0; i < a.size(); ++i) for (std::size_t j = 0; j < b.size(); ++j) { work.step(); accept(ve_cover(a, i, b, j, tol, cone_tol), false); }
    for (std::size_t i = 0; i < a.size(); ++i) for (std::size_t j = 0; j < b.size(); ++j) { work.step(); accept(ev_cover(a, i, b, j, tol, cone_tol), false); }
    for (std::size_t i = 0; i < a.size(); ++i) for (std::size_t j = 0; j < b.size(); ++j) { work.step(); accept(vv_cover(a, i, b, j, tol, cone_tol), true); }
    return result;
}
std::string covers_exact_json(const Polygon& a, const Polygon& b, const std::optional<Rational>& window,
                             bool require_in_segment, const Rational& tol, const std::optional<Rational>& cone_tol,
                             const std::optional<Rational>& seg_tol) {
    return array_json(enumerate_covers(a, b, window, require_in_segment, tol, cone_tol, seg_tol), [](const Cover& c) {
        return "{\"label\":" + label_json(c.label) + ",\"strict\":" + (c.strict ? "true" : "false")
             + ",\"window_active\":" + (c.window_active ? "true" : "false")
             + ",\"param\":" + (c.param ? ('\"' + c.param->canonical() + '\"') : std::string("null"))
             + ",\"point_a\":" + point_json(c.point_a) + ",\"point_b\":" + point_json(c.point_b)
             + ",\"gap_squared\":\"" + c.gap_squared.canonical() + "\",\"gap_sign\":" + std::to_string(c.gap_sign)
             + ",\"normal_direction\":" + (c.normal_direction ? point_json(*c.normal_direction) : std::string("null")) + '}';
    });
}

Entrance::Entrance(const Body& first, const Body& second, bool merge_convex, bool compact_subdivision, const GeometryLimits& limits)
    : compact_(compact_subdivision), limits_(limits), a(first), b(second) {
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    for (const auto* body : {&a, &b}) {
        work.check_size(body->vertices.size());
        for (const auto& p : body->vertices) check_point_bits(p, limits_);
    }
    parts_a = triangulate(a.vertices, work); parts_b = triangulate(b.vertices, work);
    if (merge_convex) { parts_a = merge_parts(std::move(parts_a), work); parts_b = merge_parts(std::move(parts_b), work); }
    if (parts_b.empty() || parts_a.empty()) throw std::logic_error("empty full-dimensional convex decomposition");
    if (parts_a.size() > limits_.max_elements / parts_b.size()) throw numeric::Error(5, "product cell limit exceeded");
    std::set<Segment> unique_edges;
    for (const auto& pa : parts_a) for (const auto& pb : parts_b) {
        if (pa.size() > limits_.max_elements / pb.size()) throw numeric::Error(5, "convex difference point limit exceeded");
        Polygon differences;
        for (const auto& va : pa) for (const auto& vb : pb) { work.step(); differences.push_back(sub(vb, va)); }
        work.check_size(differences.size());
        auto cell = hull(std::move(differences));
        for (const auto& p : cell) update_bits(statistics_, p);
        for (const auto& e : edges(cell)) unique_edges.insert(sorted_segment(e[0], e[1]));
        boxes_.push_back(numeric::exact_aabb2(cell)); cells.push_back(std::move(cell));
    }
    cell_edges.assign(unique_edges.begin(), unique_edges.end());
    work.check_size(cell_edges.size());
    statistics_.exact_work_units = work.consumed();
}
int Entrance::membership(const Point& point) const {
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    check_point_bits(point, limits_);
    int state = -1;
    for (std::size_t i = 0; i < cells.size(); ++i) {
        work.step();
        if (!boxes_[i].contains(point)) continue;
        work.step(cells[i].size());
        const auto value = cell_state(cells[i], point);
        if (value == 1) return 1;
        state = std::max(state, value);
    }
    return state;
}
int Entrance::directional_state(const Point& point, const Point& direction) const {
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    check_point_bits(point, limits_); check_point_bits(direction, limits_);
    int state = -1;
    for (std::size_t i = 0; i < cells.size(); ++i) {
        work.step(1 + cells[i].size());
        if (!boxes_[i].contains(point) || cell_state(cells[i], point) < 0) continue;
        int value = 1;
        for (const auto& e : edges(cells[i])) {
            work.step();
            const auto delta = sub(e[1], e[0]);
            if (cross(delta, sub(point, e[0])).sign()) continue;
            const auto sign = cross(delta, direction).sign();
            if (sign < 0) { value = -1; break; }
            if (!sign) value = 0;
        }
        if (value == 1) return 1;
        state = std::max(state, value);
    }
    return state;
}
int Entrance::topology(const Point& point) const {
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    check_point_bits(point, limits_);
    const auto state = membership(point);
    if (state != 0) return state;
    std::set<Point> rays;
    for (std::size_t i = 0; i < cells.size(); ++i) {
        work.step(1 + cells[i].size());
        if (!boxes_[i].contains(point) || cell_state(cells[i], point) < 0) continue;
        for (const auto& e : edges(cells[i])) {
            const auto delta = sub(e[1], e[0]);
            if (cross(delta, sub(point, e[0])).sign()) continue;
            const auto length = exact::abs(delta[0]) + exact::abs(delta[1]);
            const auto ray = mul(delta, Rational(1) / length);
            rays.insert(ray); rays.insert(mul(ray, Rational(-1)));
        }
    }
    std::vector<Point> ordered(rays.begin(), rays.end());
    std::sort(ordered.begin(), ordered.end(), angle_less);
    for (std::size_t i = 0; i < ordered.size(); ++i) {
        auto direction = add(ordered[i], ordered[(i + 1) % ordered.size()]);
        if (direction == Point{Rational(0), Rational(0)}) direction = {-ordered[i][1], ordered[i][0]};
        if (directional_state(point, direction) < 0) return 0;
    }
    return 1;
}
const std::vector<RawSegment>& Entrance::raw_segments() const {
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    if (raw_.empty()) {
        if (a.vertices.size() > limits_.max_elements / (2 * b.vertices.size())) throw numeric::Error(5, "raw segment limit exceeded");
        std::vector<RawSegment> built;
        for (std::size_t i = 0; i < a.vertices.size(); ++i) for (std::size_t j = 0; j < b.vertices.size(); ++j) {
            work.step(2);
            built.push_back({{"VE", i, j}, sub(b.vertices[j], a.vertices[i]), sub(b.vertices[(j + 1) % b.vertices.size()], a.vertices[i])});
            built.push_back({{"EV", i, j}, sub(b.vertices[j], a.vertices[i]), sub(b.vertices[j], a.vertices[(i + 1) % a.vertices.size()])});
        }
        raw_ = std::move(built);
    }
    return raw_;
}
void Entrance::build_skeleton() const {
    if (skeleton_ready_) return;
    CacheTransaction transaction(*this);
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    std::map<Segment, std::set<Label>> originals;
    for (const auto& r : raw_segments()) originals[sorted_segment(r.start, r.end)].insert(r.label);
    std::vector<Segment> segments;
    std::vector<std::set<Label>> source_labels;
    for (const auto& [segment, labels] : originals) { segments.push_back(segment); source_labels.push_back(labels); }
    const auto arranged = arrange(segments, work, &statistics_.intersection_points);
    std::map<Point, std::set<Label>> point_labels;
    std::vector<ContactSegment> contact_result;
    std::vector<Segment> boundary_result;
    for (const auto& [e, sources] : arranged) {
        std::set<Label> labels;
        for (const auto index : sources) labels.insert(source_labels[index].begin(), source_labels[index].end());
        for (const auto& p : e) { point_labels[p].insert(labels.begin(), labels.end()); update_bits(statistics_, p); }
        const auto p = middle(e[0], e[1]);
        work.step(static_cast<std::uint64_t>(cells.size()));
        if (membership(p) != 0) continue;
        const auto delta = sub(e[1], e[0]); const Point left{-delta[1], delta[0]};
        const std::array<int, 2> sides{directional_state(p, left), directional_state(p, mul(left, Rational(-1)))};
        const bool is_boundary = (sides[0] >= 0) != (sides[1] >= 0);
        contact_result.push_back({e[0], e[1], std::vector<Label>(labels.begin(), labels.end()), sides, is_boundary});
        if (is_boundary) boundary_result.push_back(e);
    }
    std::vector<ContactPoint> point_result;
    for (const auto& [point, labels] : point_labels) {
        work.step(static_cast<std::uint64_t>(cells.size()));
        if (membership(point) == 0) point_result.push_back({point, std::vector<Label>(labels.begin(), labels.end())});
    }
    if (contact_result.empty()) throw std::logic_error("contact skeleton has no boundary edges");
    contacts_ = std::move(contact_result); points_ = std::move(point_result); boundary_ = std::move(boundary_result);
    statistics_.raw_segments = raw_.size(); statistics_.arranged_segments = arranged.size();
    statistics_.exact_work_units += work.consumed(); skeleton_ready_ = true; transaction.commit();
}
const std::vector<ContactSegment>& Entrance::contact_segments() const { build_skeleton(); return contacts_; }
const std::vector<ContactPoint>& Entrance::contact_points() const { build_skeleton(); return points_; }
const std::vector<Segment>& Entrance::boundary() const { build_skeleton(); return boundary_; }
const std::vector<CoverPiece>& Entrance::clipped_covers() const {
    if (clipped_ready_) return clipped_;
    CacheTransaction transaction(*this);
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    std::vector<CoverPiece> result;
    for (const auto& raw : raw_segments()) {
        const auto side = raw.label.kind == "VE" ? ve_side_exact(a.vertices, raw.label.a_index, b.vertices, raw.label.b_index)
                                                  : ev_side_exact(a.vertices, raw.label.a_index, b.vertices, raw.label.b_index);
        if (side < 0) continue;
        std::set<Rational> parameters{Rational(0), Rational(1)};
        for (const auto& e : cell_edges) { work.step(); const auto values = cuts(raw.start, raw.end, e[0], e[1]); parameters.insert(values.begin(), values.end()); }
        auto lo = parameters.begin(), hi = lo;
        const auto direction = sub(raw.end, raw.start);
        for (++hi; hi != parameters.end(); ++lo, ++hi) {
            const auto p = add(raw.start, mul(direction, *lo)), q = add(raw.start, mul(direction, *hi)), center = middle(p, q);
            const Point left{-direction[1], direction[0]};
            const std::array<int, 2> states{directional_state(center, left), directional_state(center, mul(left, Rational(-1)))};
            result.push_back({raw.label, p, q, membership(center), states, (states[0] >= 0) != (states[1] >= 0)});
            work.check_size(result.size());
        }
    }
    clipped_ = std::move(result); clipped_ready_ = true; statistics_.exact_work_units += work.consumed(); transaction.commit();
    return clipped_;
}
const Subdivision& Entrance::subdivision() const {
    if (subdivision_ready_) return subdivision_;
    CacheTransaction transaction(*this);
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    build_skeleton();
    const auto skeleton_work = work.consumed();
    std::vector<Segment> scaffold;
    if (compact_) for (const auto& e : contacts_) scaffold.push_back({e.start, e.end});
    else scaffold = keys(arrange(cell_edges, work));
    std::set<Rational> x_values;
    const auto box = numeric::exact_aabb2([&] { Polygon p; for (const auto& e : cell_edges) { p.push_back(e[0]); p.push_back(e[1]); } return p; }());
    for (const auto& e : scaffold) for (const auto& p : e) x_values.insert(p[0]);
    for (const auto& p : points_) x_values.insert(p.point[0]);
    std::vector<Rational> xs(x_values.begin(), x_values.end());
    Subdivision result;
    std::set<Segment> face_edges;
    for (std::size_t i = 0; i + 1 < xs.size(); ++i) {
        const auto& left = xs[i]; const auto& right = xs[i + 1]; const auto center = (left + right) / Rational(2);
        std::map<Rational, std::array<Rational, 2>> levels{{box.min_y, {box.min_y, box.min_y}}, {box.max_y, {box.max_y, box.max_y}}};
        for (const auto& e : scaffold) {
            work.step();
            if (std::min(e[0][0], e[1][0]) < center && center < std::max(e[0][0], e[1][0]))
                levels[y_at(e, center)] = {y_at(e, left), y_at(e, right)};
        }
        auto low = levels.begin(), high = low;
        for (++high; high != levels.end(); ++low, ++high) {
            const Polygon raw{{left, low->second[0]}, {right, low->second[1]}, {right, high->second[1]}, {left, high->second[0]}};
            Polygon ring;
            for (std::size_t j = 0; j < raw.size(); ++j) if (raw[j] != raw[(j + raw.size() - 1) % raw.size()]) ring.push_back(raw[j]);
            const Point sample{center, (low->first + high->first) / Rational(2)};
            result.faces.push_back({ring, sample, membership(sample), topology(sample)});
            work.check_size(result.faces.size());
            for (const auto& e : edges(ring)) face_edges.insert(sorted_segment(e[0], e[1]));
        }
    }
    std::vector<Segment> face_segments(face_edges.begin(), face_edges.end());
    const auto arranged = arrange(face_segments, work);
    std::set<Point> vertices;
    for (const auto& [e, sources] : arranged) {
        (void)sources;
        std::set<Point> values{e[0], e[1]};
        for (const auto& p : points_) { work.step(); if (on_segment(p.point, e[0], e[1])) values.insert(p.point); }
        auto first = values.begin(), second = first;
        for (++second; second != values.end(); ++first, ++second) {
            const auto sample = middle(*first, *second);
            result.edges.push_back({{*first, *second}, sample, membership(sample), topology(sample)});
            work.check_size(result.edges.size());
            vertices.insert(*first); vertices.insert(*second);
        }
    }
    work.check_size(vertices.size());
    for (const auto& point : vertices) result.vertices.push_back({{point}, point, membership(point), topology(point)});
    for (const auto* layer : {&result.vertices, &result.edges, &result.faces}) for (const auto& cell : *layer) {
        for (const auto& p : cell.vertices) update_bits(statistics_, p);
        update_bits(statistics_, cell.sample);
    }
    subdivision_ = std::move(result); subdivision_ready_ = true; statistics_.exact_work_units += work.consumed() - skeleton_work; transaction.commit();
    return subdivision_;
}
const Statistics& Entrance::statistics() const { return statistics_; }
int polygons_overlap_exact(const Body& a, const Body& b, const Point& point) { return Entrance(a, b).membership(point); }
int entrance_membership_exact(const Body& a, const Body& b, const Point& point) { return Entrance(a, b).topology(point); }
std::string point_json(const Point& point) { return "[\"" + point[0].canonical() + "\",\"" + point[1].canonical() + "\"]"; }
std::string polygon_json(const Polygon& polygon) { return array_json(polygon, [](const Point& p) { return point_json(p); }); }
std::string label_json(const Label& label) { return "[\"" + label.kind + "\"," + std::to_string(label.a_index) + ',' + std::to_string(label.b_index) + ']'; }
std::string Entrance::export_exact() const {
    CacheTransaction transaction(*this);
    Work work(limits_);
    exact::IntegerLimitScope integer_scope(limits_.max_integer_bits);
    const auto& subd = subdivision();
    const auto polygons = [](const std::vector<Polygon>& values) { return array_json(values, [](const Polygon& p) { return polygon_json(p); }); };
    const auto segments = [](const std::vector<Segment>& values) { return array_json(values, [](const Segment& e) { return segment_json(e); }); };
    const auto layer = [](const std::vector<Cell>& values) { return array_json(values, [](const Cell& c) { return cell_json(c); }); };
    std::string out = "{\"schema\":\"eab2.c1.exact.v1\",\"a\":" + body_json(a) + ",\"b\":" + body_json(b)
        + ",\"parts_a\":" + polygons(parts_a) + ",\"parts_b\":" + polygons(parts_b) + ",\"cells\":" + polygons(cells)
        + ",\"cell_edges\":" + segments(cell_edges) + ",\"raw_segments\":";
    out += array_json(raw_segments(), [](const RawSegment& r) {
        return "{\"label\":" + label_json(r.label) + ",\"start\":" + point_json(r.start) + ",\"end\":" + point_json(r.end) + '}';
    });
    out += ",\"contact_segments\":" + array_json(contacts_, [](const ContactSegment& c) {
        return "{\"start\":" + point_json(c.start) + ",\"end\":" + point_json(c.end) + ",\"labels\":" + labels_json(c.labels)
             + ",\"side_states\":[" + std::to_string(c.side_states[0]) + ',' + std::to_string(c.side_states[1])
             + "],\"boundary\":" + (c.boundary ? "true" : "false") + '}';
    });
    out += ",\"contact_points\":" + array_json(points_, [](const ContactPoint& p) {
        return "{\"point\":" + point_json(p.point) + ",\"labels\":" + labels_json(p.labels) + '}';
    });
    out += ",\"covers_zero_window\":" + covers_exact_json(a.vertices, b.vertices, Rational(0));
    out += ",\"clipped_covers\":" + array_json(clipped_covers(), [](const CoverPiece& c) {
        return "{\"label\":" + label_json(c.label) + ",\"start\":" + point_json(c.start) + ",\"end\":" + point_json(c.end)
             + ",\"body_state\":" + std::to_string(c.body_state) + ",\"side_states\":[" + std::to_string(c.side_states[0])
             + ',' + std::to_string(c.side_states[1]) + "],\"exposed\":" + (c.exposed ? "true" : "false") + '}';
    });
    out += ",\"boundary\":" + segments(boundary_) + ",\"subdivision\":{\"vertices\":" + layer(subd.vertices)
         + ",\"edges\":" + layer(subd.edges) + ",\"faces\":" + layer(subd.faces) + ",\"exterior_state\":-1}";
    out += ",\"limits\":{\"max_work_units\":" + std::to_string(limits_.max_work_units)
         + ",\"max_elements\":" + std::to_string(limits_.max_elements) + ",\"max_integer_bits\":" + std::to_string(limits_.max_integer_bits) + '}';
    out += ",\"statistics\":{\"raw_segments\":" + std::to_string(statistics_.raw_segments)
         + ",\"arranged_segments\":" + std::to_string(statistics_.arranged_segments)
         + ",\"intersection_points\":" + std::to_string(statistics_.intersection_points)
         + ",\"cells\":" + std::to_string(cells.size()) + ",\"contact_segments\":" + std::to_string(contacts_.size())
         + ",\"contact_points\":" + std::to_string(points_.size()) + ",\"max_integer_bits\":" + std::to_string(statistics_.max_integer_bits)
         + ",\"max_integer_bits_scope\":\"stored_exact_coordinates\",\"intersection_points_scope\":\"closed_intersections_including_shared_and_overlap_endpoints\""
         + ",\"exact_work_units\":" + std::to_string(statistics_.exact_work_units) + ",\"floating_filters\":0,\"exact_fallbacks\":0}}";
    transaction.commit();
    return out;
}
} // namespace eab2::geometry2
