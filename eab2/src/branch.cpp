#include "branch.hpp"
#include "geometry_seed.hpp"
#include "numeric.hpp"
#include <algorithm>
#include <set>
#include <sstream>

namespace eab2::statics::branch_detail {
namespace {
using P = Polynomial;
using PV = std::vector<P>;
using PM = std::vector<PV>;
void trim(P& p) {
    for (auto i = p.terms.begin(); i != p.terms.end();) {
        if (i->second == Rational(0)) i = p.terms.erase(i); else ++i;
    }
    if (p.terms.size() > 8192) throw exact::ResourceLimit("branch polynomial term limit");
}
P monomial(unsigned e, unsigned h, const Rational& q = Rational(1)) {
    P p; if (q != Rational(0)) p.terms[{e, h}] = q; return p;
}
Rational pow(Rational q, unsigned n) { Rational r(1); while (n--) r = r * q; return r; }
Rational value(const P& p, const Rational& e, const Rational& h) {
    Rational r;
    for (const auto& [degree, q] : p.terms) r = r + q * pow(e, degree.first) * pow(h, degree.second);
    return r;
}
Rational coefficient(const P& p, unsigned e, unsigned h) {
    const auto at = p.terms.find({e, h}); return at == p.terms.end() ? Rational(0) : at->second;
}
std::string quote(const std::string& text) {
    std::string s = "\"";
    for (char c : text) { if (c == '"' || c == '\\') s += '\\'; s += c; }
    return s + '"';
}
template<class R, class F> std::string array(const R& r, F f) {
    std::string s = "["; bool first = true;
    for (const auto& q : r) { if (!first) s += ','; first = false; s += f(q); }
    return s + ']';
}
std::string json(const P& p) {
    return array(p.terms, [](const auto& t) { return '[' + std::to_string(t.first.first) + ',' +
        std::to_string(t.first.second) + ',' + quote(t.second.canonical()) + ']'; });
}
std::string indices(const std::vector<std::size_t>& v) {
    return array(v, [](auto k) { return std::to_string(k); });
}
struct Family { PM A; PV b, c; };
Family family(const LimitProblem2& base, const GeometrySeed2& seed, int direction,
              const Rational& mu0, const Rational& slope, int side) {
    // Rebuild every polynomial from original affine primitives. In particular,
    // force has degree two and contact moment degree three in epsilon.
    const P epsilon = monomial(1, 0, Rational(direction));
    const P mu = P(mu0) + monomial(1, 0, slope) + monomial(1, 1, Rational(side));
    std::map<std::pair<std::string, std::size_t>, Point> vertices, velocity;
    std::map<Point, Point> contact_velocity;
    std::map<std::string, BodySeed2> bodies;
    for (const auto& body : base.contact_set.assembly.bodies) for (std::size_t k = 0; k < body.geometry.vertices.size(); ++k)
        vertices[{body.body_id, body.geometry.original_vertex_ids[k]}] = body.geometry.vertices[k];
    for (const auto& v : seed.vertices) {
        velocity[{v.body_id, v.vertex_id}] = v.derivative;
        contact_velocity[vertices.at({v.body_id, v.vertex_id})] = v.derivative;
    }
    for (const auto& b : seed.bodies) bodies[b.body_id] = b;
    const auto m = base.b.size(), n = base.c.size();
    Family out{PM(m, PV(n)), PV(m), PV(n)}; out.c.back() = P(Rational(1));
    auto affine = [&](const Rational& q, const Rational& d) { return P(q) + epsilon * P(d); };
    std::size_t j = 0;
    for (const auto& contact : base.contact_set.constraints) {
        const auto& label = contact.label;
        const auto key0 = std::make_pair(label.edge_body, label.edge[0]);
        const auto key1 = std::make_pair(label.edge_body, label.edge[1]);
        const auto raw_t = geometry2::sub(vertices.at(key1), vertices.at(key0));
        const Rational sense = raw_t == contact.tangent ? Rational(1) : Rational(-1);
        if (geometry2::mul(raw_t, sense) != contact.tangent) throw std::logic_error("branch original tangent mismatch");
        const auto dt = geometry2::mul(geometry2::sub(velocity.at(key1), velocity.at(key0)), sense);
        const auto dp = contact_velocity.at(contact.point);
        const P tx = affine(contact.tangent[0], dt[0]), ty = affine(contact.tangent[1], dt[1]);
        const P px = affine(contact.point[0], dp[0]), py = affine(contact.point[1], dp[1]);
        for (int sign : {-1, 1}) {
            const P fx = -ty + P(Rational(sign)) * mu * tx, fy = tx + P(Rational(sign)) * mu * ty;
            std::size_t row = 0;
            for (std::size_t k = 0; k < base.contact_set.assembly.bodies.size(); ++k) {
                const auto& body = base.contact_set.assembly.bodies[k];
                if (body.boundary_type == "FIXED_BODY") continue;
                const auto& d = bodies.at(body.body_id);
                const P factor(Rational(static_cast<int>(k == contact.a) - static_cast<int>(k == contact.b)));
                const P ax = affine(body.dof_anchor[0], d.dof_anchor[0]);
                const P ay = affine(body.dof_anchor[1], d.dof_anchor[1]);
                const std::array<P, 3> wrench{factor * fx, factor * fy, factor * ((px - ax) * fy - (py - ay) * fx)};
                for (std::size_t axis = 0; axis < 3; ++axis) if (body.dof_mask[axis]) out.A[row++][j] = wrench[axis];
            }
            ++j;
        }
    }
    std::size_t row = 0;
    for (std::size_t k = 0; k < base.contact_set.assembly.bodies.size(); ++k) {
        const auto& body = base.contact_set.assembly.bodies[k];
        if (body.boundary_type == "FIXED_BODY") continue;
        const auto& d = bodies.at(body.body_id);
        const P ax = affine(body.dof_anchor[0] - body.reference_point[0], d.dof_anchor[0]);
        const P ay = affine(body.dof_anchor[1] - body.reference_point[1], d.dof_anchor[1]);
        auto wrench = [&](const Wrench& v, const Wrench& dv) {
            const P x = affine(v[0], dv[0]), y = affine(v[1], dv[1]);
            return std::array<P, 3>{x, y, affine(v[2], dv[2]) - ax * y + ay * x};
        };
        const auto live = wrench(base.loads[k].live, d.live), dead = wrench(base.loads[k].dead, d.dead);
        for (std::size_t axis = 0; axis < 3; ++axis) if (body.dof_mask[axis]) {
            out.A[row][j] = live[axis]; out.b[row++] = -dead[axis];
        }
    }
    return out;
}
Matrix values(const PM& p, const Rational& e, const Rational& h) {
    Matrix out; for (const auto& row : p) { Vector v; for (const auto& q : row) v.push_back(value(q, e, h)); out.push_back(v); } return out;
}
Vector values(const PV& p, const Rational& e, const Rational& h) {
    Vector out; for (const auto& q : p) out.push_back(value(q, e, h)); return out;
}
PM transpose(const PM& a, std::size_t n) {
    PM out(n, PV(a.size())); for (std::size_t i = 0; i < a.size(); ++i) for (std::size_t j = 0; j < n; ++j) out[j][i] = a[i][j]; return out;
}
struct Selection { std::vector<std::size_t> rows, columns; };
Selection select(Matrix a, const std::vector<std::size_t>& row_order, const std::vector<std::size_t>& column_order) {
    Matrix b; for (auto i : row_order) { Vector v; for (auto j : column_order) v.push_back(a[i][j]); b.push_back(v); }
    auto ids = row_order;
    Selection out;
    for (std::size_t col = 0; col < column_order.size() && out.rows.size() < b.size(); ++col) {
        const auto r = out.rows.size(); auto pivot = r;
        while (pivot < b.size() && b[pivot][col] == Rational(0)) ++pivot;
        if (pivot == b.size()) continue;
        std::swap(b[r], b[pivot]); std::swap(ids[r], ids[pivot]);
        const auto scale = b[r][col];
        for (std::size_t j = col; j < column_order.size(); ++j) b[r][j] = b[r][j] / scale;
        for (std::size_t i = r + 1; i < b.size(); ++i) {
            const auto factor = b[i][col];
            for (std::size_t j = col; j < column_order.size(); ++j) b[i][j] = b[i][j] - factor * b[r][j];
        }
        out.rows.push_back(ids[r]); out.columns.push_back(column_order[col]);
    }
    return out;
}
std::vector<std::size_t> range(std::size_t n) { std::vector<std::size_t> v; for (std::size_t i = 0; i < n; ++i) v.push_back(i); return v; }
// Greedy exact rank selection in a given order (Gauss-Jordan), the Python
// referee's _rank_columns rule; used to build referee-style witness bases so
// that C++ never certifies less than the referee on a degenerate probe.
std::vector<std::size_t> independent(const std::vector<Vector>& vectors, const std::vector<std::size_t>& order) {
    std::vector<Vector> reduced; std::vector<std::size_t> pivots, chosen;
    for (const auto k : order) {
        Vector v = vectors[k];
        for (std::size_t r = 0; r < reduced.size(); ++r) {
            const auto p = pivots[r];
            if (v[p] != Rational(0)) { const auto f = v[p] / reduced[r][p]; for (std::size_t j = 0; j < v.size(); ++j) v[j] = v[j] - f * reduced[r][j]; }
        }
        std::size_t p = 0; while (p < v.size() && v[p] == Rational(0)) ++p;
        if (p == v.size()) continue;
        for (std::size_t r = 0; r < reduced.size(); ++r) if (reduced[r][p] != Rational(0)) {
            const auto f = reduced[r][p] / v[p]; for (std::size_t j = 0; j < v.size(); ++j) reduced[r][j] = reduced[r][j] - f * v[j];
        }
        reduced.push_back(v); pivots.push_back(p); chosen.push_back(k);
    }
    return chosen;
}
std::vector<std::size_t> referee_rows(const Matrix& a) { return independent(a, range(a.size())); }
std::vector<std::size_t> referee_columns(const Matrix& a, const std::vector<std::size_t>& rows, const std::vector<std::size_t>& order) {
    std::vector<Vector> columns(a.empty() ? 0 : a[0].size(), Vector(rows.size()));
    for (std::size_t i = 0; i < rows.size(); ++i) for (std::size_t j = 0; j < columns.size(); ++j) columns[j][i] = a[rows[i]][j];
    return independent(columns, order);
}
std::vector<std::size_t> support_first(const Vector& x, std::optional<std::size_t> excluded) {
    std::vector<std::size_t> order;
    for (std::size_t j = 0; j < x.size(); ++j) if (x[j] != Rational(0) && (!excluded || j != *excluded)) order.push_back(j);
    for (std::size_t j = 0; j < x.size(); ++j) if (x[j] == Rational(0) && (!excluded || j != *excluded)) order.push_back(j);
    return order;
}
struct Formula {
    P denominator{Rational(1)};
    PV numerators;
    Selection selection;
    Rational epsilon, eta;
};
// Fraction-free elimination with one complete common denominator. Exact
// division is checked at every step; no expression or series is truncated.
std::optional<Formula> lift(const PM& a, const PV& rhs, const Selection& pick, std::size_t width,
                          const Rational& e, const Rational& h) {
    const auto n = pick.rows.size();
    Formula f; f.numerators.resize(width); f.selection = pick; f.epsilon = e; f.eta = h;
    if (!n) return f;
    PM b(n, PV(n + 1));
    for (std::size_t i = 0; i < n; ++i) { for (std::size_t j = 0; j < n; ++j) b[i][j] = a[pick.rows[i]][pick.columns[j]]; b[i][n] = rhs[pick.rows[i]]; }
    P previous(Rational(1));
    for (std::size_t k = 0; k + 1 < n; ++k) {
        auto pivot = k; while (pivot < n && b[pivot][k].zero()) ++pivot;
        if (pivot == n) return std::nullopt;
        std::swap(b[k], b[pivot]);
        const P diagonal = b[k][k];
        for (std::size_t i = k + 1; i < n; ++i) {
            for (std::size_t j = k + 1; j <= n; ++j) b[i][j] = divide_exact(b[i][j] * diagonal - b[i][k] * b[k][j], previous);
            b[i][k] = P();
        }
        previous = diagonal;
    }
    f.denominator = b.back()[n - 1];
    if (f.denominator.zero()) return std::nullopt;
    PV result(n);
    for (std::size_t i = n; i-- > 0;) {
        P v = b[i][n] * f.denominator;
        for (std::size_t j = i + 1; j < n; ++j) v = v - b[i][j] * result[j];
        result[i] = divide_exact(v, b[i][i]);
    }
    for (std::size_t i = 0; i < n; ++i) f.numerators[pick.columns[i]] = result[i];
    return f;
}
bool equality(const PM& a, const PV& b, const Formula& f, bool nonnegative) {
    if (f.denominator.zero()) return false;
    if (nonnegative) for (const auto& p : f.numerators) if (p.sign() * f.denominator.sign() < 0) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        P residual = -b[i] * f.denominator;
        for (std::size_t j = 0; j < f.numerators.size(); ++j) residual = residual + a[i][j] * f.numerators[j];
        if (!residual.zero()) return false;
    }
    return true;
}
// K-ordered dual-simplex repair of a primal witness (point or normalized
// ray): while some basic component is negative in K, Bland's rule pivots
// the smallest such column out and the smallest nonbasic column with a
// negative K pivot entry in. The objective is zero, so every such entering
// column passes the ratio test. Only selects a basis; the caller still
// verifies equality and K signs (acceptance 2026-10-25: the LP core returned
// the same K-infeasible degenerate vertex on every probe for t1b/06 and
// t1b/15 single_face reverse).
std::optional<Formula> k_repair(const PM& a, const PV& b, Formula f, std::size_t width,
                                const Rational& e, const Rational& h) {
    constexpr int LIMIT = 32;
    const auto at = transpose(a, width);
    for (int step = 0; step < LIMIT; ++step) {
        const int d = f.denominator.sign();
        if (d == 0) return std::nullopt;
        std::optional<std::size_t> leave;
        for (std::size_t k = 0; k < f.selection.columns.size(); ++k) {
            const auto j = f.selection.columns[k];
            if (f.numerators[j].sign() * d < 0 && (!leave || j < f.selection.columns[*leave])) leave = k;
        }
        if (!leave) return f;
        PV unit(width);
        unit[f.selection.columns[*leave]] = P(Rational(1));
        Selection transposed; transposed.rows = f.selection.columns; transposed.columns = f.selection.rows;
        const auto z = lift(at, unit, transposed, a.size(), e, h);
        if (!z) return std::nullopt;
        const int dz = z->denominator.sign();
        std::optional<std::size_t> enter;
        for (std::size_t j = 0; j < width && !enter; ++j) {
            if (std::find(f.selection.columns.begin(), f.selection.columns.end(), j) != f.selection.columns.end()) continue;
            P pivot;
            for (const auto r : f.selection.rows) pivot = pivot + z->numerators[r] * a[r][j];
            if (pivot.sign() * dz < 0) enter = j;
        }
        if (!enter) return std::nullopt;
        Selection next = f.selection; next.columns[*leave] = *enter;
        const auto lifted = lift(a, b, next, width, e, h);
        if (!lifted) return std::nullopt;
        f = *lifted;
    }
    return std::nullopt;
}
// A K-nonnegative primal witness is nonnegative at every rational point with
// eta small enough and epsilon small enough relative to eta, but not
// necessarily at the grid point it was lifted at. Record the first point of a
// finer dyadic schedule where it is, so the certificate stays independently
// verifiable at its recorded probe (the probe is not a theorem premise).
bool record_primal_probe(Formula& f) {
    for (const unsigned b : {4u, 8u, 12u, 16u, 24u, 32u, 48u, 64u}) for (const unsigned m : {2u, 4u, 8u}) {
        const Rational h(exact::Int(1), exact::Int(1) << b), e(exact::Int(1), exact::Int(1) << (b * m));
        const auto d = value(f.denominator, e, h);
        if (d == Rational(0)) continue;
        bool ok = true;
        for (const auto& q : f.numerators) if ((value(q, e, h) * d).sign() < 0) { ok = false; break; }
        if (ok) { f.epsilon = e; f.eta = h; return true; }
    }
    return false;
}
bool dual_feasible(const Family& p, const Formula& f) {
    if (f.denominator.zero()) return false;
    for (std::size_t j = 0; j < p.c.size(); ++j) {
        P residual = -p.c[j] * f.denominator;
        for (std::size_t i = 0; i < p.A.size(); ++i) residual = residual + p.A[i][j] * f.numerators[i];
        if (residual.sign() * f.denominator.sign() < 0) return false;
    }
    return true;
}
std::optional<Formula> dual_formula(const Family& p, const Vector& y, const Rational& e, const Rational& h) {
    const auto q = transpose(p.A, p.c.size());
    const auto a = values(q, e, h); const auto c = values(p.c, e, h);
    std::vector<std::size_t> tight;
    for (std::size_t j = 0; j < a.size(); ++j) {
        Rational slack = -c[j]; for (std::size_t i = 0; i < y.size(); ++i) slack = slack + a[j][i] * y[i];
        if (slack == Rational(0)) tight.push_back(j);
    }
    return lift(q, p.c, select(a, tight, range(y.size())), y.size(), e, h);
}
std::optional<Vector> probe_dual(const Matrix& a, const Vector& c, const opt::Result& primal, const opt::Options& options) {
    if (primal.status == opt::Status::optimal) return primal.exact_y;
    if (primal.status != opt::Status::infeasible) return std::nullopt;
    // The lower theorem only needs a dual feasible point. An infeasible
    // primal is NOT a reason to discard a valid mechanism: max c.x over
    // {Ax = 0, x >= 0} is OPTIMAL exactly when A^T y >= c is solvable, and
    // its exact dual is a basic point with m independent tight columns. A
    // split-variable witness LP need not return such a vertex, and then no
    // lower formula can be lifted from it (acceptance 2026-10-23).
    const auto homogeneous = opt::maximize(a, Vector(a.size()), c, options);
    if (homogeneous.status != opt::Status::optimal) return std::nullopt;
    return homogeneous.exact_y;
}
std::optional<Formula> primal_formula(const PM& a, const PV& b, const Vector& x, const Rational& e, const Rational& h) {
    if (std::all_of(b.begin(), b.end(), [](const P& q) { return q.zero(); })) {
        Formula zero; zero.numerators.resize(x.size()); zero.epsilon = e; zero.eta = h; return zero;
    }
    auto columns = range(x.size());
    std::stable_sort(columns.begin(), columns.end(), [&](auto i, auto j) { return (x[i] != Rational(0)) > (x[j] != Rational(0)); });
    return lift(a, b, select(values(a, e, h), range(a.size()), columns), x.size(), e, h);
}
std::string formula_json(const Formula& f, const LimitProblem2& base, const std::string& kind) {
    auto columns = f.selection.columns, rows = f.selection.rows;
    if (kind == "dual") std::swap(columns, rows);
    if (kind == "ray") {
        std::erase(columns, base.c.size() - 1); std::erase(rows, base.b.size());
    }
    const auto labels = array(columns, [&](auto i) {
        return export_exact(base.column_labels[i]);
    });
    return "{\"denominator\":" + json(f.denominator) + ",\"numerators\":" + array(f.numerators, [](const P& p) { return json(p); }) +
        ",\"basis\":" + indices(columns) + ",\"rows\":" + indices(rows) + ",\"labels\":" + labels +
        ",\"probe\":{\"epsilon\":" + quote(f.epsilon.canonical()) + ",\"eta\":" + quote(f.eta.canonical()) + "}}";
}
struct CandidateComponent {
    Rational slope, mu, parameter;
    ColumnLabel2 label;
    Selection selection;
    bool dual;
    std::size_t index;
    // Nonempty only for an actually acquired singular candidate branch.
    unsigned leading_epsilon_order = 0;
    Vector leading_polynomial;
};
void add_candidate(std::vector<Rational>& candidates, const Rational& s) {
    if (candidates.size() < 64 && std::find(candidates.begin(), candidates.end(), s) == candidates.end()) candidates.push_back(s);
}
using Uni = Vector;
void uni_trim(Uni& a) { while (!a.empty() && a.back() == Rational(0)) a.pop_back(); }
Rational uni_value(const Uni& a, const Rational& x) { Rational r; for (auto i = a.rbegin(); i != a.rend(); ++i) r = r * x + *i; return r; }
Uni remainder(Uni a, const Uni& b) {
    while (a.size() >= b.size() && !a.empty()) {
        const auto k = a.size() - b.size(); const auto scale = a.back() / b.back();
        for (std::size_t j = 0; j < b.size(); ++j) a[k + j] = a[k + j] - scale * b[j];
        uni_trim(a);
    }
    return a;
}
Uni quotient_exact(Uni a, const Uni& b) {
    if (b.empty()) throw std::logic_error("branch univariate zero divisor");
    Uni result(a.size() >= b.size() ? a.size() - b.size() + 1 : 0);
    while (a.size() >= b.size() && !a.empty()) {
        const auto k = a.size() - b.size(); const auto scale = a.back() / b.back();
        result[k] = scale;
        for (std::size_t j = 0; j < b.size(); ++j) a[k + j] = a[k + j] - scale * b[j];
        uni_trim(a);
    }
    if (!a.empty()) throw std::logic_error("branch univariate nonexact division");
    uni_trim(result); return result;
}
void roots_of_leading(const P& p, std::vector<Rational>& candidates) {
    if (p.zero()) return;
    const auto degree = p.terms.begin()->first.first;
    Uni u;
    for (const auto& [powers, q] : p.terms) if (powers.first == degree) {
        if (u.size() <= powers.second) u.resize(powers.second + 1);
        u[powers.second] = q;
    }
    uni_trim(u); if (u.size() < 2) return;
    Uni derivative; for (std::size_t i = 1; i < u.size(); ++i) derivative.push_back(Rational(static_cast<std::int64_t>(i)) * u[i]);
    // A repeated root can make every member of a non-square-free Sturm chain
    // vanish at a subdivision endpoint. Ignoring those zeros would then hide
    // another root on one side (e.g. v^2*(v-7/128) at v=0). Remove the exact
    // gcd only for candidate isolation; serialized leading evidence below
    // retains the original polynomial and every root multiplicity.
    Uni first = u, second = derivative;
    while (!second.empty()) { auto r = remainder(first, second); first = std::move(second); second = std::move(r); }
    if (first.size() > 1) {
        u = quotient_exact(u, first);
        derivative.clear();
        for (std::size_t i = 1; i < u.size(); ++i) derivative.push_back(Rational(static_cast<std::int64_t>(i)) * u[i]);
    }
    std::vector<Uni> sturm{u, derivative};
    while (!sturm.back().empty()) {
        Uni r = remainder(sturm[sturm.size() - 2], sturm.back());
        if (r.empty()) break;
        for (auto& q : r) q = -q;
        sturm.push_back(r);
    }
    auto variations = [&](const Rational& x) {
        int previous = 0, count = 0;
        for (const auto& poly : sturm) { const int sign = uni_value(poly, x).sign(); if (!sign) continue; if (previous && previous != sign) ++count; previous = sign; }
        return count;
    };
    Rational bound(1);
    for (std::size_t i = 0; i + 1 < u.size(); ++i) if (Rational(1) + exact::abs(u[i] / u.back()) > bound) bound = Rational(1) + exact::abs(u[i] / u.back());
    struct Interval { Rational lo, hi; unsigned depth; };
    std::vector<Interval> stack{{-bound, bound, 0}};
    std::size_t budget = 0;
    while (!stack.empty() && ++budget <= 4096 && candidates.size() < 64) {
        const auto [lo, hi, depth] = stack.back(); stack.pop_back();
        if (variations(lo) == variations(hi)) continue;
        for (const auto& s : Vector{lo, hi, critical_detail::rational_candidate2(lo, hi)})
            if (uni_value(u, s) == Rational(0)) add_candidate(candidates, s);
        if (depth >= 96) continue;
        const auto mid = (lo + hi) / Rational(2);
        if (uni_value(u, mid) == Rational(0)) add_candidate(candidates, mid);
        stack.push_back({mid, hi, depth + 1}); stack.push_back({lo, mid, depth + 1});
    }
}
void singular_candidates(const LimitProblem2& base, const GeometrySeed2& path, int direction,
                         const Formula& probed, bool dual, std::vector<Rational>& candidates,
                         std::vector<CandidateComponent>& components) {
    // eta here is a symbolic trial slope v, not a sign approximation. The
    // leading epsilon coefficients give exact rational root candidates even
    // when the acquired basis is singular at (mu*, epsilon=0).
    auto p = family(base, path, direction, base.mu, Rational(0), 1);
    PM a = dual ? transpose(p.A, p.c.size()) : p.A;
    PV b = dual ? p.c : PV(p.A.size());
    if (!dual) { a.push_back(p.c); b.emplace_back(Rational(1)); }
    const auto f = lift(a, b, probed.selection, dual ? base.b.size() : base.c.size(), Rational(0), Rational(0));
    if (!f) return;
    auto record = [&](const P& root, std::size_t index) {
        if (root.zero()) return;
        const auto degree = root.terms.begin()->first.first;
        Vector leading;
        for (const auto& [powers, q] : root.terms) if (powers.first == degree) {
            if (leading.size() <= powers.second) leading.resize(powers.second + 1);
            leading[powers.second] = q;
        }
        uni_trim(leading);
        if (leading.size() < 2) return;
        const auto scale = leading.back();
        for (auto& q : leading) q = q / scale;
        components.push_back({Rational(0), Rational(0), Rational(0), base.column_labels[index],
            probed.selection, dual, index, degree, leading});
    };
    if (dual) {
        for (std::size_t j = 0; j < p.c.size(); ++j) {
            P root = -p.c[j] * f->denominator;
            for (std::size_t i = 0; i < p.A.size(); ++i) root = root + p.A[i][j] * f->numerators[i];
            roots_of_leading(root, candidates);
            record(root, j);
        }
    } else for (std::size_t j = 0; j < f->numerators.size(); ++j) {
        const auto& root = f->numerators[j];
        roots_of_leading(root, candidates);
        // r_alpha=1 is a normalization, not a root constraint. Its numerator
        // can vanish with its denominator and must never acquire a tied label.
        if (j + 1 != base.c.size() && std::find(probed.selection.columns.begin(), probed.selection.columns.end(), j) != probed.selection.columns.end()) record(root, j);
    }
}
// Candidate generation is deliberately not a proof. It differentiates a basis
// acquired at a nearby rational point, then leaves every branch decision to K.
void candidates_from(const LimitProblem2& base, const GeometrySeed2& path, int direction,
                     const Formula& probed, bool dual, std::vector<Rational>& candidates,
                     std::vector<CandidateComponent>& components, bool allow_singular) {
    auto p = family(base, path, direction, base.mu, Rational(0), 0);
    auto pmu = family(base, path, 0, base.mu, Rational(1), 0);
    PM a = dual ? transpose(p.A, p.c.size()) : p.A;
    PM amu = dual ? transpose(pmu.A, pmu.c.size()) : pmu.A;
    PV b = dual ? p.c : PV(p.A.size());
    if (!dual) { a.push_back(p.c); amu.push_back(pmu.c); b.emplace_back(Rational(1)); }
    auto f = lift(a, b, probed.selection, dual ? base.b.size() : base.c.size(), Rational(0), Rational(0));
    auto fm = lift(amu, b, probed.selection, dual ? base.b.size() : base.c.size(), Rational(0), Rational(0));
    if (!f || !fm) { if (allow_singular) singular_candidates(base, path, direction, probed, dual, candidates, components); return; }
    const auto d0 = coefficient(f->denominator, 0, 0), dm0 = coefficient(fm->denominator, 0, 0);
    if (d0 == Rational(0) || dm0 == Rational(0)) { if (allow_singular) singular_candidates(base, path, direction, probed, dual, candidates, components); return; }
    PV roots, muroots;
    if (dual) {
        for (std::size_t j = 0; j < base.c.size(); ++j) {
            P root = -p.c[j] * f->denominator, mr = -pmu.c[j] * fm->denominator;
            for (std::size_t i = 0; i < base.b.size(); ++i) {
                root = root + p.A[i][j] * f->numerators[i]; mr = mr + pmu.A[i][j] * fm->numerators[i];
            }
            roots.push_back(root); muroots.push_back(mr);
        }
    } else { roots = f->numerators; muroots = fm->numerators; }
    for (std::size_t j = 0; j < roots.size(); ++j) {
        if (coefficient(roots[j], 0, 0) != Rational(0)) continue;
        const auto dp = coefficient(roots[j], 1, 0) / d0, dm = coefficient(muroots[j], 1, 0) / dm0;
        if (dm == Rational(0)) continue;
        const Rational s = -dp / dm;
        add_candidate(candidates, s);
        if ((dual && dm < Rational(0)) || (!dual && dm > Rational(0)))
            components.push_back({s, dm, dp, base.column_labels[j], probed.selection, dual, j});
    }
}
struct Direction {
    std::optional<Rational> slope;
    std::optional<Formula> lower, point, ray;
    std::string reason = "threshold_branch_certificate_unavailable";
    std::vector<CandidateComponent> components;
    std::size_t candidate_count = 0, attempts = 0;
};
// Candidate generation only: the exact threshold of the probed geometry at a
// fixed small epsilon, bisected in mu over the original domain (the feasible
// force cone nests in mu), and the simplest rational of its quotient bracket.
// Candidate roots of one LP vertex are basis dependent on degenerate critical
// faces; this route does not depend on which vertex the LP core returns.
// Whether the slope is the derivative is decided by K alone.
std::vector<Rational> probe_threshold_candidates(const LimitProblem2& base, const GeometrySeed2& path, int direction,
        const CriticalParameter2& critical, const SensitivityOptions2& options) {
    std::vector<Rational> out;
    const Rational mu_star = *critical.exact_threshold, mu_max = *critical.original_mu_max;
    for (unsigned ee : {24u}) {
        const Rational e(exact::Int(1), exact::Int(1) << ee);
        // Every matrix entry is affine in mu, so two evaluated families give
        // A(mu) = A0 + mu (A1 - A0) without rebuilding polynomials per step.
        const auto zero = family(base, path, direction, Rational(0), Rational(0), 0);
        const auto one = family(base, path, direction, Rational(1), Rational(0), 0);
        const auto a0 = values(zero.A, e, Rational(0)), a1 = values(one.A, e, Rational(0));
        const auto b = values(zero.b, e, Rational(0)), c = values(zero.c, e, Rational(0));
        const auto unbounded = [&](const Rational& mu) {
            Matrix a = a0;
            for (std::size_t i = 0; i < a.size(); ++i) for (std::size_t j = 0; j < a[i].size(); ++j) a[i][j] = a0[i][j] + mu * (a1[i][j] - a0[i][j]);
            return opt::maximize(a, b, c, options.lp_options).status == opt::Status::unbounded;
        };
        Rational lo(0), hi = mu_max;
        if (!unbounded(hi) || unbounded(lo)) continue;
        for (int step = 0; step < 56; ++step) { const Rational mid = (lo + hi) / Rational(2); if (unbounded(mid)) hi = mid; else lo = mid; }
        out.push_back(critical_detail::rational_candidate2((lo - mu_star) / e, (hi - mu_star) / e));
    }
    return out;
}
bool valid_original_domain(const CriticalParameter2& critical) {
    if (critical.original_mu_min != Rational(0) || !critical.original_mu_max || !critical.exact_threshold ||
        *critical.original_mu_max < Rational(0) || !critical_detail::is_binary64(*critical.original_mu_max) ||
        *critical.exact_threshold < Rational(0) || *critical.exact_threshold > *critical.original_mu_max) return false;
    if (critical.original_mu_max_bits) {
        try { if (numeric::decode_binary64(*critical.original_mu_max_bits) != *critical.original_mu_max) return false; }
        catch (const numeric::Error&) { return false; }
    }
    return true;
}
Direction certify(const CriticalParameter2& critical, const LimitSeed2& seed, int direction,
                  const SensitivityOptions2& options, const SensitivityResult2& old) {
    Direction out;
    if (!seed.geometry_path || !valid_original_domain(critical)) return out;
    if (options.test_witnessless_slope) { out.slope = Rational(0); out.reason.clear(); return out; }
    const auto& base = *critical.threshold_certificate->problem;
    geometry2::GeometryWorkScope work(base.contact_set.assembly.limits);
    exact::IntegerLimitScope integers(base.contact_set.assembly.limits.max_integer_bits);
    const auto& path = *seed.geometry_path;
    std::vector<Rational> candidates;
    for (const auto& c : old.implicit_components) add_candidate(candidates, Rational(direction) * c.slope);
    add_candidate(candidates, Rational(0));
    bool boundary = false;
    std::set<std::string> collected;
    // Every witness basis seen on any probe of this direction (own style and
    // referee style). Bases only select; K and the rational probe check decide.
    std::vector<Selection> seen_lower, seen_point, seen_ray_aug, seen_ray_py;
    const auto remember = [](std::vector<Selection>& seen, const Selection& s) {
        if (s.rows.size() != s.columns.size() || s.rows.empty()) return;
        for (const auto& old : seen) if (old.rows == s.rows && old.columns == s.columns) return;
        seen.push_back(s);
    };
    auto collect = [&](const Formula& f, bool dual, bool allow_singular) {
        const auto key = std::string(dual ? "d" : "r") + (allow_singular ? "s" : "n") + indices(f.selection.rows) + indices(f.selection.columns);
        if (collected.insert(key).second) candidates_from(base, path, direction, f, dual, candidates, out.components, allow_singular);
    };
    bool extended = false;
    for (std::size_t at = 0; at < candidates.size(); ++at) {
        const auto slope = candidates[at];
        const P lower_mu = P(*critical.exact_threshold) + monomial(1, 0, slope) - monomial(1, 1);
        const P upper_gap = P(*critical.original_mu_max - *critical.exact_threshold) - monomial(1, 0, slope) - monomial(1, 1);
        const bool domain_ok = lower_mu.sign() >= 0 && upper_gap.sign() >= 0;
        if (!domain_ok) boundary = true;
        const auto low = family(base, path, direction, *critical.exact_threshold, slope, -1);
        const auto high = family(base, path, direction, *critical.exact_threshold, slope, 1);
        // Screening probe (same as the referee): one LP pair at a small point.
        // Only a candidate whose lower side is bounded and whose upper side is
        // unbounded there can carry a sandwich; the others still contribute
        // their bases as candidates but skip the probe grid and the lifts.
        bool screened = false;
        {
            ++out.attempts;
            const Rational se(exact::Int(1), exact::Int(1) << 24), sh(exact::Int(1), exact::Int(1) << 8);
            const auto a_low = values(low.A, se, sh), a_high = values(high.A, se, sh);
            const auto b_low = values(low.b, se, sh), b_high = values(high.b, se, sh);
            const auto c = values(low.c, se, sh);
            const auto lower = opt::maximize(a_low, b_low, c, options.lp_options);
            const auto upper = opt::maximize(a_high, b_high, c, options.lp_options);
            const auto screen_y = probe_dual(a_low, c, lower, options.lp_options);
            if (screen_y) { const auto f = dual_formula(low, *screen_y, se, sh); if (f) collect(*f, true, true); }
            if (const auto y = probe_dual(a_high, c, upper, options.lp_options)) { const auto f = dual_formula(high, *y, se, sh); if (f) collect(*f, true, true); }
            if (upper.status == opt::Status::unbounded) {
                PM a = high.A; a.push_back(high.c); PV b(high.b.size()); b.emplace_back(Rational(1));
                const auto normalized = opt::solve(values(a, se, sh), values(b, se, sh), Vector(c.size()), options.lp_options);
                const auto f = normalized.status == opt::Status::optimal ? primal_formula(a, b, normalized.exact_x, se, sh) : std::nullopt;
                if (f) collect(*f, false, true);
            }
            // Same rule as the referee: a lower dual witness (from the
            // homogeneous LP when the primal is infeasible) and an unbounded
            // upper side are both required to enter the grid.
            screened = !screen_y || upper.status != opt::Status::unbounded;
        }
        for (unsigned eh : screened ? std::vector<unsigned>{} : std::vector<unsigned>{4u, 8u, 12u, 16u}) for (unsigned ee : {8u, 16u, 24u, 32u}) {
            ++out.attempts;
            const Rational e(exact::Int(1), exact::Int(1) << ee), h(exact::Int(1), exact::Int(1) << eh);
            const auto a_low = values(low.A, e, h), a_high = values(high.A, e, h);
            const auto b_low = values(low.b, e, h), b_high = values(high.b, e, h);
            const auto c = values(low.c, e, h);
            auto lower = opt::maximize(a_low, b_low, c, options.lp_options);
            auto upper = opt::maximize(a_high, b_high, c, options.lp_options);
            std::optional<Formula> probed_lower_dual, probed_upper_ray, referee_lower_dual, referee_upper_ray;
            const std::size_t alpha = c.size() - 1;
            // Referee-style dual basis: independent rows of A in index order,
            // basis = independent tight columns in index order. Candidate
            // roots are basis dependent on degenerate duals, so the referee's
            // basis is always collected beside this backend's own basis.
            const auto referee_dual = [&](const Matrix& a, const Vector& y) {
                const auto rows_y = referee_rows(a);
                std::vector<std::size_t> tight;
                for (std::size_t j = 0; j < c.size(); ++j) {
                    Rational slack = -c[j];
                    for (std::size_t i = 0; i < a.size(); ++i) slack = slack + a[i][j] * y[i];
                    if (slack == Rational(0)) tight.push_back(j);
                }
                Formula pf; pf.selection.rows = referee_columns(a, rows_y, tight); pf.selection.columns = rows_y; pf.epsilon = e; pf.eta = h;
                return pf;
            };
            const auto lower_y = probe_dual(a_low, c, lower, options.lp_options);
            if (lower_y) {
                const auto f = dual_formula(low, *lower_y, e, h);
                if (f) { probed_lower_dual = f; collect(*f, true, false); remember(seen_lower, f->selection); if (dual_feasible(low, *f)) out.lower = f; }
                referee_lower_dual = referee_dual(a_low, *lower_y);
                collect(*referee_lower_dual, true, false);
                remember(seen_lower, referee_lower_dual->selection);
            }
            if (const auto y = probe_dual(a_high, c, upper, options.lp_options)) {
                const auto f = dual_formula(high, *y, e, h);
                if (f) collect(*f, true, true);
                collect(referee_dual(a_high, *y), true, true);
            }
            PM a_aug = high.A; a_aug.push_back(high.c); PV b_aug(high.b.size()); b_aug.emplace_back(Rational(1));
            std::optional<Formula> own_point, own_ray;
            if (upper.status == opt::Status::unbounded) {
                // Acquire BFS candidates from the feasibility polyhedra, not
                // only the ray representation returned by a value LP.
                const auto feasible = opt::solve(a_high, b_high, Vector(c.size()), options.lp_options);
                const auto normalized = opt::solve(values(a_aug, e, h), values(b_aug, e, h), Vector(c.size()), options.lp_options);
                const auto point = feasible.status == opt::Status::optimal ? primal_formula(high.A, high.b, feasible.exact_x, e, h) : std::nullopt;
                const auto ray = normalized.status == opt::Status::optimal ? primal_formula(a_aug, b_aug, normalized.exact_x, e, h) : std::nullopt;
                own_point = point; own_ray = ray;
                if (point) { remember(seen_point, point->selection); if (equality(high.A, high.b, *point, true)) out.point = point; }
                if (ray) { probed_upper_ray = ray; collect(*ray, false, false); remember(seen_ray_aug, ray->selection); if (equality(a_aug, b_aug, *ray, true)) out.ray = ray; }
                // The value LP's own UNBOUNDED witnesses (feasible point and
                // normalized improving ray) come from a different vertex walk
                // than the feasibility LPs above; lift them too.
                if (!out.point && !upper.exact_x.empty()) {
                    const auto f = primal_formula(high.A, high.b, upper.exact_x, e, h);
                    if (f) { remember(seen_point, f->selection); if (equality(high.A, high.b, *f, true)) out.point = f; }
                }
                if (!out.ray && !upper.exact_ray.empty()) {
                    Vector scaled = upper.exact_ray;
                    const auto drive = scaled[alpha];
                    if (drive > Rational(0)) {
                        for (auto& v : scaled) v = v / drive;
                        const auto f = primal_formula(a_aug, b_aug, scaled, e, h);
                        if (f) { remember(seen_ray_aug, f->selection); if (equality(a_aug, b_aug, *f, true)) out.ray = f; }
                    }
                }
            }
            if (lower.status == opt::Status::unbounded) {
                PM a = low.A; a.push_back(low.c); PV b(low.b.size()); b.emplace_back(Rational(1));
                const auto normalized = opt::solve(values(a, e, h), values(b, e, h), Vector(c.size()), options.lp_options);
                const auto f = normalized.status == opt::Status::optimal ? primal_formula(a, b, normalized.exact_x, e, h) : std::nullopt;
                if (f) collect(*f, false, true);
            }
            // Witness acquisition is basis dependent on degenerate probes: a
            // formula lifted from this probe's own basis may fail in K while a
            // basis seen on another probe, or the referee-style basis, passes
            // here. Bases only select; K is the proof, and a reused basis must
            // also be nonnegative at this rational probe so the recorded probe
            // stays independently verifiable.
            const auto probe_primal_ok = [&](const Formula& f) {
                const auto d = value(f.denominator, e, h); if (d == Rational(0)) return false;
                for (const auto& p : f.numerators) if ((value(p, e, h) * d).sign() < 0) return false;
                return true;
            };
            const auto probe_dual_ok = [&](const Formula& f) {
                const auto d = value(f.denominator, e, h); if (d == Rational(0)) return false;
                for (std::size_t j = 0; j < c.size(); ++j) {
                    Rational slack = -c[j] * d;
                    for (std::size_t i = 0; i < a_low.size(); ++i) slack = slack + a_low[i][j] * value(f.numerators[i], e, h);
                    if ((slack * d).sign() < 0) return false;
                }
                return true;
            };
            // Only the most recent bases are retried (RETRY_LIMIT, same as the
            // referee): every lift is a polynomial elimination.
            constexpr std::size_t RETRY_LIMIT = 6;
            const auto recent = [](const std::vector<Selection>& seen) {
                std::vector<Selection> out(seen.end() - std::min(seen.size(), RETRY_LIMIT), seen.end());
                std::reverse(out.begin(), out.end()); return out;
            };
            if (!out.lower) for (const auto& s : recent(seen_lower)) {
                const auto f = lift(transpose(low.A, low.c.size()), low.c, s, low.b.size(), e, h);
                if (f && dual_feasible(low, *f) && probe_dual_ok(*f)) { out.lower = f; break; }
            }
            if (!out.point) for (const auto& s : recent(seen_point)) {
                const auto f = lift(high.A, high.b, s, high.c.size(), e, h);
                if (f && equality(high.A, high.b, *f, true) && probe_primal_ok(*f)) { out.point = f; break; }
            }
            if (!out.ray) for (const auto& s : recent(seen_ray_aug)) {
                const auto f = lift(a_aug, b_aug, s, high.c.size(), e, h);
                if (f && equality(a_aug, b_aug, *f, true) && probe_primal_ok(*f)) { out.ray = f; break; }
            }
            if (!out.ray) for (const auto& s : recent(seen_ray_py)) {
                PV rhs; for (const auto& row : high.A) rhs.push_back(-row[alpha]);
                auto f = lift(high.A, rhs, s, high.c.size(), e, h);
                if (f) { f->numerators[alpha] = f->denominator; if (equality(a_aug, b_aug, *f, true) && probe_primal_ok(*f)) { out.ray = f; break; } }
            }
            // The LP core may return the same degenerate vertex on every
            // probe. After the retry window, visit further vertices along the
            // failing coordinates (same rule as the referee: maximize each
            // negative component at the fixed screening point, at most
            // TARGETED_LIMIT of them) and lift each one at this probe at once.
            // Bases only select; K and the rational probe check decide.
            constexpr std::size_t TARGETED_LIMIT = 8;
            const auto failing = [](const Formula& f) {
                std::vector<std::size_t> out; const int d = f.denominator.sign();
                for (std::size_t j = 0; j < f.numerators.size(); ++j) if (f.numerators[j].sign() * d < 0) out.push_back(j);
                return out;
            };
            const Rational te(exact::Int(1), exact::Int(1) << 24), th(exact::Int(1), exact::Int(1) << 8);
            if (!out.point && own_point) { std::size_t visited = 0; const Matrix a_t = values(high.A, te, th); const Vector b_t = values(high.b, te, th);
                for (const auto j : failing(*own_point)) {
                    if (++visited > TARGETED_LIMIT) break;
                    Vector goal(c.size()); goal[j] = Rational(1);
                    const auto vertex = opt::maximize(a_t, b_t, goal, options.lp_options);
                    if (vertex.status != opt::Status::optimal) continue;
                    const auto rows = referee_rows(a_t);
                    Selection py; py.rows = rows; py.columns = referee_columns(a_t, rows, support_first(vertex.exact_x, std::nullopt));
                    for (const auto& s : std::vector<Selection>{select(a_t, range(a_t.size()), support_first(vertex.exact_x, std::nullopt)), py}) {
                        remember(seen_point, s);
                        const auto f = lift(high.A, high.b, s, high.c.size(), e, h);
                        if (f && equality(high.A, high.b, *f, true) && probe_primal_ok(*f)) { out.point = f; break; }
                    }
                    if (out.point) break;
                } }
            if (!out.ray && own_ray) { std::size_t visited = 0; const Matrix a_t = values(high.A, te, th), a_t_aug = values(a_aug, te, th); const Vector b_t_aug = values(b_aug, te, th);
                for (const auto j : failing(*own_ray)) {
                    if (++visited > TARGETED_LIMIT) break;
                    Vector goal(c.size()); goal[j] = Rational(1);
                    const auto vertex = opt::maximize(a_t_aug, b_t_aug, goal, options.lp_options);
                    if (vertex.status != opt::Status::optimal) continue;
                    const Selection aug = select(a_t_aug, range(a_t_aug.size()), support_first(vertex.exact_x, std::nullopt));
                    remember(seen_ray_aug, aug);
                    if (const auto f = lift(a_aug, b_aug, aug, high.c.size(), e, h); f && equality(a_aug, b_aug, *f, true) && probe_primal_ok(*f)) { out.ray = f; break; }
                    const auto rows = referee_rows(a_t);
                    Selection py; py.rows = rows; py.columns = referee_columns(a_t, rows, support_first(vertex.exact_x, alpha));
                    remember(seen_ray_py, py);
                    PV rhs; for (const auto& row : high.A) rhs.push_back(-row[alpha]);
                    auto f = lift(high.A, rhs, py, high.c.size(), e, h);
                    if (f) { f->numerators[alpha] = f->denominator; if (equality(a_aug, b_aug, *f, true) && probe_primal_ok(*f)) { out.ray = f; break; } }
                } }
            // Last resort for this probe: K-ordered repair of the own witness,
            // recorded at the first finer probe where it is nonnegative.
            if (!out.point && own_point) if (auto f = k_repair(high.A, high.b, *own_point, high.c.size(), e, h);
                    f && equality(high.A, high.b, *f, true) && record_primal_probe(*f)) { remember(seen_point, f->selection); out.point = f; }
            if (!out.ray && own_ray) if (auto f = k_repair(a_aug, b_aug, *own_ray, high.c.size(), e, h);
                    f && equality(a_aug, b_aug, *f, true) && record_primal_probe(*f)) { remember(seen_ray_aug, f->selection); out.ray = f; }
            if (out.lower && out.point && out.ray) {
                if (domain_ok) { out.slope = slope; out.reason.clear(); }
                else out.reason = "threshold_search_domain_boundary";
                out.candidate_count = candidates.size();
                return out;
            }
            // A correct-side basis may also be singular at the base point.
            // If the bracket is not yet proved, its leading roots can expose
            // the competing branch just as a wrong-side probe can.
            if (probed_lower_dual) collect(*probed_lower_dual, true, true);
            if (probed_upper_ray) collect(*probed_upper_ray, false, true);
            if (referee_lower_dual) collect(*referee_lower_dual, true, true);
            if (referee_upper_ray) collect(*referee_upper_ray, false, true);
        }
        out.lower.reset(); out.point.reset(); out.ray.reset();
        if (at + 1 == candidates.size() && !extended) {
            // All vertex-derived candidates failed: extend once with the probed
            // geometry's own exact thresholds (on a boundary threshold this can
            // still expose the inward branch; outward sandwiches stay refused).
            extended = true;
            for (const auto& s : probe_threshold_candidates(base, path, direction, critical, options)) add_candidate(candidates, s);
        }
    }
    if (boundary) out.reason = "threshold_search_domain_boundary";
    out.candidate_count = candidates.size();
    return out;
}
std::string direction_json(const Direction& d, const LimitProblem2& base) {
    const auto component = [&](const CandidateComponent& c) {
        if (!c.leading_polynomial.empty()) return "{\"label\":" + export_exact(c.label) + ",\"s\":" + quote(d.slope->canonical()) +
            ",\"index\":" + std::to_string(c.index) + ",\"leading_epsilon_order\":" + std::to_string(c.leading_epsilon_order) +
            ",\"leading_polynomial\":" + array(c.leading_polynomial, [](const Rational& q) { return quote(q.canonical()); }) + '}';
        return "{\"label\":" + export_exact(c.label) + ",\"s\":" + quote(c.slope.canonical()) +
            ",\"partial_mu\":" + quote(c.mu.canonical()) + ",\"partial_parameter\":" + quote(c.parameter.canonical()) +
            ",\"index\":" + std::to_string(c.index) + '}';
    };
    std::map<std::string, std::vector<CandidateComponent>> branches;
    if (d.slope) for (const auto& c : d.components) if (c.leading_polynomial.empty() ? c.slope == *d.slope : uni_value(c.leading_polynomial, *d.slope) == Rational(0)) {
        auto columns = c.selection.columns, rows = c.selection.rows;
        if (c.dual) std::swap(columns, rows);
        if (!c.dual) { std::erase(columns, base.c.size() - 1); std::erase(rows, base.b.size()); }
        const auto key = "{\"kind\":" + quote(c.dual ? "dual" : "ray") + ",\"basis\":" + indices(columns) +
            ",\"rows\":" + indices(rows) + (c.leading_polynomial.empty() ? "" : ",\"singular\":true");
        auto& group = branches[key];
        if (std::none_of(group.begin(), group.end(), [&](const auto& old) { return old.index == c.index; })) group.push_back(c);
    }
    return "{\"status\":" + quote(d.slope ? "certified" : "unresolved") + ",\"reason\":" + (d.reason.empty() ? "null" : quote(d.reason)) +
        ",\"s\":" + (d.slope ? quote(d.slope->canonical()) : "null") +
        ",\"lower\":" + (d.slope && d.lower ? formula_json(*d.lower, base, "dual") : "null") +
        ",\"upper\":" + (d.slope && d.point && d.ray ? "{\"point\":" + formula_json(*d.point, base, "point") + ",\"ray\":" + formula_json(*d.ray, base, "ray") + '}' : "null") +
        ",\"candidate_count\":" + std::to_string(d.candidate_count) + ",\"attempts\":" + std::to_string(d.attempts) +
        ",\"candidate_branches\":" + array(branches, [&](const auto& group) { return group.first + ",\"components\":" + array(group.second, component) + '}'; }) + '}';
}
} // namespace
P operator+(P a, const P& b) { for (const auto& [m, q] : b.terms) a.terms[m] = a.terms[m] + q; trim(a); return a; }
P operator-(P a, const P& b) { for (const auto& [m, q] : b.terms) a.terms[m] = a.terms[m] - q; trim(a); return a; }
P operator-(const P& a) { P r; for (const auto& [m, q] : a.terms) r.terms[m] = -q; return r; }
P operator*(const P& a, const P& b) {
    P r;
    for (const auto& [ma, qa] : a.terms) for (const auto& [mb, qb] : b.terms) {
        const std::pair<unsigned, unsigned> m{ma.first + mb.first, ma.second + mb.second};
        if (m.first > 256 || m.second > 256) throw exact::ResourceLimit("branch polynomial degree limit");
        r.terms[m] = r.terms[m] + qa * qb;
    }
    trim(r); return r;
}
P divide_exact(P a, const P& b) {
    if (b.zero()) throw std::logic_error("branch polynomial zero divisor");
    P result;
    const auto [bm, bq] = *b.terms.rbegin();
    while (!a.zero()) {
        const auto [am, aq] = *a.terms.rbegin();
        if (am.first < bm.first || am.second < bm.second) throw std::logic_error("branch Bareiss nonexact division");
        const P term = monomial(am.first - bm.first, am.second - bm.second, aq / bq);
        result = result + term; a = a - term * b;
    }
    return result;
}
SensitivityResult2 certified_threshold(const CriticalParameter2& critical, const LimitSeed2& seed,
    const SensitivityOptions2& options, const SensitivityResult2& old) {
    SensitivityResult2 out;
    out.mathematical_status = critical.mathematical_status; out.parameter = options.parameter;
    out.validity_conditions = {"L1接触骨架不变"};
    for (const auto& c : options.validity_conditions) if (std::find(out.validity_conditions.begin(), out.validity_conditions.end(), c) == out.validity_conditions.end()) out.validity_conditions.push_back(c);
    for (const auto& c : critical.validity_conditions) if (std::find(out.validity_conditions.begin(), out.validity_conditions.end(), c) == out.validity_conditions.end()) out.validity_conditions.push_back(c);
    out.method = "branch_certificate"; out.quality = "approximate";
    Direction forward, reverse;
    if (seed.geometry_path && seed.geometry_path->mu != Rational(0)) { out.call_status = "INVALID_INPUT"; out.reason = "threshold_mu_seed_not_allowed"; return out; }
    if (seed.geometry_path) {
        const auto& p = *critical.threshold_certificate->problem;
        const auto rebuilt = family(p, *seed.geometry_path, 1, p.mu, Rational(0), 0);
        bool valid = true;
        for (std::size_t i = 0; i < p.A.size(); ++i) {
            valid = valid && coefficient(rebuilt.b[i], 0, 0) == p.b[i] && coefficient(rebuilt.b[i], 1, 0) == seed.db[i];
            for (std::size_t j = 0; j < p.c.size(); ++j) valid = valid && coefficient(rebuilt.A[i][j], 0, 0) == p.A[i][j] && coefficient(rebuilt.A[i][j], 1, 0) == seed.dA[i][j];
        }
        for (std::size_t j = 0; j < p.c.size(); ++j) valid = valid && coefficient(rebuilt.c[j], 0, 0) == p.c[j] && coefficient(rebuilt.c[j], 1, 0) == seed.dc[j];
        if (!valid) { out.call_status = "INVALID_INPUT"; out.reason = "affine_seed_mismatch"; return out; }
    }
    auto attempt = [&](int direction) {
        try { return certify(critical, seed, direction, options, old); }
        catch (const exact::ResourceLimit&) { return Direction(); }
    };
    // Independent attempts: exhausting one finite resource budget must not
    // erase a certificate in the other direction or silently fill that side.
    if (options.positive_direction_valid) forward = attempt(1);
    else forward.reason = "direction_outside_validity_conditions";
    if (options.negative_direction_valid) reverse = attempt(-1);
    else reverse.reason = "direction_outside_validity_conditions";
    // Invariant: a certified direction carries all three ordered-field
    // witnesses; a value without them is never emitted (acceptance gate).
    for (auto* d : {&forward, &reverse}) if (d->slope && !(d->lower && d->point && d->ray)) {
        d->slope.reset(); d->lower.reset(); d->point.reset(); d->ray.reset(); d->reason = "internal_certificate_shape";
    }
    const auto& base = *critical.threshold_certificate->problem;
    out.branch_certificate = "{\"version\":1,\"order\":\"epsilon_then_eta\",\"search_domain\":" + export_search_domain(critical) +
        ",\"forward\":" + direction_json(forward, base) + ",\"reverse\":" + direction_json(reverse, base) + '}';
    if (forward.slope) out.directional_derivative = out.right_derivative = forward.slope;
    if (reverse.slope) out.left_derivative = -*reverse.slope;
    if (forward.slope && reverse.slope) out.differentiability = out.right_derivative == out.left_derivative ? "smooth" : "one_sided";
    else if (forward.slope || reverse.slope) out.differentiability = "one_sided";
    else { out.differentiability = "unresolved"; out.quality = "approximate"; }
    if (!forward.slope || !reverse.slope) out.reason = forward.reason == "threshold_search_domain_boundary" || reverse.reason == "threshold_search_domain_boundary" ? "threshold_search_domain_boundary" : !forward.slope ? forward.reason : reverse.reason;
    // A singular candidate is not a proof of discontinuity, and cannot block
    // another K-certified branch. Only after both directions remain unproved
    // retain the conservative certificate-singularity diagnostic (no jet).
    if (!forward.slope && !reverse.slope && seed.geometry_path && valid_original_domain(critical) &&
        options.positive_direction_valid && options.negative_direction_valid &&
        out.reason != "threshold_search_domain_boundary" && old.differentiability == "singular" &&
        (old.reason == "critical_basis_singular" || old.reason == "zero_implicit_denominator")) {
        out.differentiability = "singular"; out.reason = old.reason;
    }
    if (forward.slope || reverse.slope) { out.display_status = "EXACT"; out.quality = "exact_jet"; }
    std::set<std::string> labels;
    for (const auto* d : {&forward, &reverse}) if (d->slope) for (const auto& c : d->components) if ((c.leading_polynomial.empty() ? c.slope == *d->slope : uni_value(c.leading_polynomial, *d->slope) == Rational(0)) && labels.insert(export_exact(c.label)).second) {
        out.tied_labels.push_back(c.label);
        if (!c.leading_polynomial.empty()) continue; // No invented first-order quotient at a singular basis.
        const auto ordinary = d == &forward ? c.slope : -c.slope;
        out.implicit_components.push_back({c.label, ordinary, c.mu, d == &forward ? c.parameter : -c.parameter, c.index});
        out.piece_jacobians.push_back({c.label, ordinary});
    }
    return out;
}
} // namespace eab2::statics::branch_detail
