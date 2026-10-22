#if defined(__AVX__)
#error eab2 controlled sources require the x64 SSE2 compilation target
#endif
#include "critical.hpp"
#include "numeric.hpp"
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace eab2::statics {
namespace {
using P = Polynomial2;
using PM = PolynomialMatrix2;
using exact::Int;

bool nonzero(const P& a) { return std::any_of(a.begin(), a.end(), [](const auto& x) { return x != Rational(0); }); }
P trim(P a) {
    while (a.size() > 1 && a.back() == Rational(0)) a.pop_back();
    if (a.empty()) a.emplace_back(0);
    return a;
}
P scale(const P& a, const Rational& factor) {
    P out;
    for (const auto& x : a) out.push_back(x * factor);
    return trim(std::move(out));
}
P subtract(const P& a, const P& b) {
    P out(std::max(a.size(), b.size()));
    for (std::size_t i = 0; i < out.size(); ++i)
        out[i] = (i < a.size() ? a[i] : Rational(0)) - (i < b.size() ? b[i] : Rational(0));
    return trim(std::move(out));
}
P multiply(const P& a, const P& b) {
    P out(a.size() + b.size() - 1);
    for (std::size_t i = 0; i < a.size(); ++i)
        for (std::size_t j = 0; j < b.size(); ++j) out[i + j] = out[i + j] + a[i] * b[j];
    return trim(std::move(out));
}
Rational evaluate(const P& p, const Rational& x) {
    Rational out;
    for (auto i = p.rbegin(); i != p.rend(); ++i) out = out * x + *i;
    return out;
}
std::pair<P, P> divide(P a, const P& divisor) {
    a = trim(std::move(a));
    const P b = trim(divisor);
    if (!nonzero(b)) throw std::logic_error("polynomial division by zero");
    if (a.size() < b.size()) return {{Rational(0)}, std::move(a)};
    P quotient(a.size() - b.size() + 1);
    while (a.size() >= b.size() && nonzero(a)) {
        const auto shift = a.size() - b.size();
        const auto factor = a.back() / b.back();
        quotient[shift] = factor;
        for (std::size_t i = 0; i < b.size(); ++i) a[i + shift] = a[i + shift] - factor * b[i];
        a = trim(std::move(a));
    }
    return {trim(std::move(quotient)), std::move(a)};
}
P derivative(const P& p) {
    P out;
    for (std::size_t i = 1; i < p.size(); ++i)
        out.push_back(Rational(Int::decimal(std::to_string(i))) * p[i]);
    return trim(std::move(out));
}
P positive_normalize(const P& p) {
    return nonzero(p) ? scale(p, Rational(1) / exact::abs(p.back())) : p;
}
std::size_t variations(const std::vector<P>& sequence, const Rational& x) {
    int previous = 0;
    std::size_t count = 0;
    for (const auto& p : sequence) {
        const int sign = evaluate(p, x).sign();
        if (!sign) continue;
        if (previous && sign != previous) ++count;
        previous = sign;
    }
    return count;
}
std::size_t root_count(const P& p, const Rational& lo, const Rational& hi) {
    if (lo > hi || p.size() < 2) return 0;
    if (lo == hi) return evaluate(p, lo) == Rational(0) ? 1 : 0;
    std::vector<P> sturm{positive_normalize(p), positive_normalize(derivative(p))};
    while (nonzero(sturm.back())) {
        auto remainder = divide(sturm[sturm.size() - 2], sturm.back()).second;
        if (!nonzero(remainder)) break;
        sturm.push_back(positive_normalize(scale(remainder, Rational(-1))));
    }
    const auto left = variations(sturm, lo), right = variations(sturm, hi);
    const auto endpoint = evaluate(p, lo) == Rational(0) ? 1u : 0u;
    if (left + endpoint < right) throw std::logic_error("invalid Sturm variation count");
    return left + endpoint - right;
}
P determinant(PM work) {
    const auto n = work.size();
    if (!n) return {Rational(1)};
    for (const auto& row : work) if (row.size() != n) throw std::invalid_argument("square polynomial matrix required");
    P previous{Rational(1)};
    int sign = 1;
    for (std::size_t k = 0; k + 1 < n; ++k) {
        std::size_t pivot = k;
        while (pivot < n && !nonzero(work[pivot][k])) ++pivot;
        if (pivot == n) return {Rational(0)};
        if (pivot != k) { std::swap(work[k], work[pivot]); sign = -sign; }
        const P value = work[k][k];
        for (std::size_t i = k + 1; i < n; ++i) {
            for (std::size_t j = k + 1; j < n; ++j) {
                auto qr = divide(subtract(multiply(value, work[i][j]), multiply(work[i][k], work[k][j])), previous);
                if (nonzero(qr.second)) throw std::logic_error("nonexact polynomial elimination");
                work[i][j] = std::move(qr.first);
            }
            work[i][k] = {Rational(0)};
        }
        previous = value;
    }
    return scale(work.back().back(), Rational(sign));
}
std::vector<std::size_t> rank_columns(const Matrix& A, const std::vector<std::size_t>& order) {
    std::vector<Vector> vectors;
    std::vector<std::size_t> pivots, basis;
    if (A.empty()) return basis;
    for (const auto j : order) {
        Vector vector;
        for (const auto& row : A) vector.push_back(row[j]);
        for (std::size_t k = 0; k < vectors.size(); ++k) {
            const auto factor = vector[pivots[k]];
            for (std::size_t i = 0; i < vector.size(); ++i) vector[i] = vector[i] - factor * vectors[k][i];
        }
        std::size_t pivot = 0;
        while (pivot < vector.size() && vector[pivot] == Rational(0)) ++pivot;
        if (pivot == vector.size()) continue;
        const auto factor = vector[pivot];
        for (auto& v : vector) v = v / factor;
        vectors.push_back(std::move(vector));
        pivots.push_back(pivot);
        basis.push_back(j);
        if (basis.size() == A.size()) break;
    }
    return basis;
}
PM basis_matrix(const PM& matrix, const std::vector<std::size_t>& basis) {
    PM out;
    for (const auto& row : matrix) {
        std::vector<P> target;
        for (auto j : basis) target.push_back(row[j]);
        out.push_back(std::move(target));
    }
    return out;
}
std::pair<P, std::array<std::size_t, 2>> remove_endpoint_roots(P p, const Rational& lo, const Rational& hi) {
    std::array<std::size_t, 2> orders{0, 0};
    const std::array<Rational, 2> endpoints{lo, hi};
    for (std::size_t k = 0; k < 2; ++k) {
        while (p.size() > 1 && evaluate(p, endpoints[k]) == Rational(0)) {
            auto qr = divide(p, {-endpoints[k], Rational(1)});
            if (nonzero(qr.second)) throw std::logic_error("endpoint factor verification failed");
            p = std::move(qr.first);
            ++orders[k];
        }
    }
    return {std::move(p), orders};
}
Int floor(const Rational& x) {
    Int q = x.numerator() / x.denominator();
    if (x.sign() < 0 && x.numerator() % x.denominator() != Int(0)) q = q - Int(1);
    return q;
}
Rational power_two(std::int64_t exponent) {
    return exponent >= 0 ? Rational(Int(1) << static_cast<std::size_t>(exponent))
        : Rational(Int(1), Int(1) << static_cast<std::size_t>(-exponent));
}
} // namespace

namespace critical_detail {
bool is_binary64(const Rational& q) {
    if (q == Rational(0)) return true;
    auto n = exact::abs(q.numerator());
    const auto d = q.denominator();
    const auto dbits = d.bit_length();
    if (d != (Int(1) << (dbits - 1))) return false;
    std::size_t trailing = 0;
    while (!n.odd()) { n = n >> 1; ++trailing; }
    const auto width = n.bit_length();
    const auto exponent = static_cast<std::int64_t>(trailing) - static_cast<std::int64_t>(dbits - 1);
    return width <= 53 && exponent >= -1074 && exponent + static_cast<std::int64_t>(width) - 1 <= 1023;
}
std::optional<Rational> binary_midpoint(const Rational& lo, const Rational& hi) {
    if (lo < Rational(0) || lo >= hi) return std::nullopt;
    const auto mid = (lo + hi) / Rational(2);
    if (is_binary64(mid)) return mid;
    auto exponent = static_cast<std::int64_t>(mid.numerator().bit_length()) -
        static_cast<std::int64_t>(mid.denominator().bit_length());
    if (mid < power_two(exponent)) --exponent;
    exponent = std::max<std::int64_t>(exponent - 52, -1074);
    const auto unit = power_two(exponent);
    auto candidate = Rational(floor(mid / unit)) * unit;
    if (candidate <= lo) candidate = candidate + unit;
    return lo < candidate && candidate < hi ? std::optional<Rational>(candidate) : std::nullopt;
}
PolynomialMatrix2 affine_matrix2(const LimitProblem2& zero, const LimitProblem2& one) {
    if (zero.A.size() != one.A.size() || zero.b != one.b || zero.c != one.c)
        throw std::invalid_argument("fixed geometry and loads required");
    PM out;
    for (std::size_t i = 0; i < zero.A.size(); ++i) {
        if (zero.A[i].size() != one.A[i].size()) throw std::invalid_argument("fixed matrix shape required");
        std::vector<P> row;
        for (std::size_t j = 0; j < zero.A[i].size(); ++j)
            row.push_back({zero.A[i][j], one.A[i][j] - zero.A[i][j]});
        out.push_back(std::move(row));
    }
    return out;
}
std::optional<CriticalBasis2> mechanism_basis2(const LimitResult2& result, const PM& matrix) {
    if (result.mathematical_status != "OPTIMAL" || !result.problem || !result.exact_y) return std::nullopt;
    const auto& p = *result.problem;
    const auto m = p.A.size(), n = p.c.size();
    if (result.exact_y->size() != m) return std::nullopt;
    std::vector<std::size_t> active;
    for (std::size_t j = 0; j < n; ++j) {
        Rational value;
        for (std::size_t i = 0; i < m; ++i) value = value + p.A[i][j] * (*result.exact_y)[i];
        if (value == p.c[j]) active.push_back(j);
    }
    const auto basis = rank_columns(p.A, active);
    if (basis.size() != m) return std::nullopt;
    const auto B = basis_matrix(matrix, basis);
    const auto det = determinant(B);
    const auto denominator = evaluate(det, p.mu);
    if (denominator == Rational(0)) return std::nullopt;
    std::vector<P> numerators;
    Vector values;
    for (std::size_t j = 0; j < n; ++j) {
        P numerator{Rational(0)};
        if (std::find(basis.begin(), basis.end(), j) == basis.end()) {
            PM bordered = B;
            for (std::size_t i = 0; i < m; ++i) bordered[i].push_back(matrix[i][j]);
            std::vector<P> bottom;
            for (const auto k : basis) bottom.push_back({p.c[k]});
            bottom.push_back({p.c[j]});
            bordered.push_back(std::move(bottom));
            numerator = scale(determinant(std::move(bordered)), Rational(-1));
        }
        const auto value = evaluate(numerator, p.mu) / denominator;
        if (value < Rational(0)) return std::nullopt;
        numerators.push_back(std::move(numerator));
        values.push_back(value);
    }
    return CriticalBasis2{"mechanism", basis, std::nullopt, det, std::move(numerators), p.column_labels, p.mu, std::move(values)};
}
std::optional<CriticalBasis2> improving_basis2(const LimitResult2& result, const PM& matrix) {
    if (result.mathematical_status != "UNBOUNDED" || !result.problem || !result.improving_ray) return std::nullopt;
    const auto& p = *result.problem;
    const auto m = p.A.size(), n = p.c.size();
    if (result.improving_ray->size() != n) return std::nullopt;
    std::vector<std::size_t> objective;
    for (std::size_t j = 0; j < n; ++j) if (p.c[j] != Rational(0)) objective.push_back(j);
    if (objective.size() != 1 || p.c[objective[0]] != Rational(1)) return std::nullopt;
    const auto entering = objective[0];
    std::vector<std::size_t> order;
    for (std::size_t j = 0; j < n; ++j) if (j != entering && (*result.improving_ray)[j] > Rational(0)) order.push_back(j);
    for (std::size_t j = 0; j < n; ++j)
        if (j != entering && std::find(order.begin(), order.end(), j) == order.end()) order.push_back(j);
    const auto basis = rank_columns(p.A, order);
    if (basis.size() != m) return std::nullopt;
    const auto B = basis_matrix(matrix, basis);
    const auto det = determinant(B);
    const auto denominator = evaluate(det, p.mu);
    if (denominator == Rational(0)) return std::nullopt;
    std::vector<P> numerators;
    Vector values;
    std::vector<ColumnLabel2> labels;
    for (std::size_t k = 0; k < m; ++k) {
        auto replaced = B;
        for (std::size_t i = 0; i < m; ++i) replaced[i][k] = scale(matrix[i][entering], Rational(-1));
        auto numerator = determinant(std::move(replaced));
        const auto value = evaluate(numerator, p.mu) / denominator;
        if (value < Rational(0)) return std::nullopt;
        numerators.push_back(std::move(numerator));
        values.push_back(value);
        labels.push_back(p.column_labels[basis[k]]);
    }
    return CriticalBasis2{"improving_ray", basis, entering, det, std::move(numerators), std::move(labels), p.mu, std::move(values)};
}
std::optional<BranchSigns2> branch_signs2(const std::optional<CriticalBasis2>& branch,
                                       const Rational& lower, const Rational& upper) {
    if (!branch || lower > upper) return std::nullopt;
    if (lower == upper) return BranchSigns2{};
    const auto sample = (lower + upper) / Rational(2);
    const auto reduced = remove_endpoint_roots(branch->determinant, lower, upper);
    if (!nonzero(reduced.first) || root_count(reduced.first, lower, upper)) return std::nullopt;
    const auto denominator = evaluate(branch->determinant, sample);
    BranchSigns2 proofs{{std::nullopt, reduced.second, denominator}};
    for (std::size_t k = 0; k < branch->numerators.size(); ++k) {
        const auto& poly = branch->numerators[k];
        if (!nonzero(poly)) { proofs.push_back({k, {0, 0}, Rational(0)}); continue; }
        const auto numerator = remove_endpoint_roots(poly, lower, upper);
        if (root_count(numerator.first, lower, upper)) return std::nullopt;
        const auto value = evaluate(poly, sample) / denominator;
        if (value < Rational(0)) return std::nullopt;
        proofs.push_back({k, numerator.second, value});
    }
    return proofs;
}
Rational rational_candidate2(const Rational& lower, const Rational& upper) {
    if (lower > upper) throw std::invalid_argument("ordered rational interval required");
    if (lower == upper) return lower;
    std::vector<Int> shifts;
    auto lo = lower, hi = upper;
    Rational value;
    for (;;) {
        const auto a = floor(lo), b = floor(hi);
        if (lo == Rational(a)) { value = Rational(a); break; }
        if (a < b) { value = Rational(a + Int(1)); break; }
        shifts.push_back(a);
        const auto nextlo = Rational(1) / (hi - Rational(a));
        hi = Rational(1) / (lo - Rational(a));
        lo = nextlo;
    }
    for (auto i = shifts.rbegin(); i != shifts.rend(); ++i) value = Rational(*i) + Rational(1) / value;
    return value;
}
bool candidate_is_boundary2(const Rational& candidate,
    const std::optional<CriticalBasis2>& lower, const std::optional<CriticalBasis2>& upper) {
    if (candidate == Rational(0)) return true;
    for (const auto* branch : {&lower, &upper}) {
        if (!*branch) continue;
        const auto& b = **branch;
        if (nonzero(b.determinant) && evaluate(b.determinant, candidate) == Rational(0)) return true;
        for (const auto& p : b.numerators) if (nonzero(p) && evaluate(p, candidate) == Rational(0)) return true;
    }
    return false;
}
} // namespace critical_detail

namespace {
CriticalParameter2 finish_critical(const contact::ContactSet2& contacts, const Loads2& loads,
    const Rational& lo, const Rational& hi, const LimitResult2& low, const LimitResult2& high,
    const std::string& reason, std::size_t count, const opt::Options& options) {
    using namespace critical_detail;
    CriticalParameter2 answer;
    answer.mathematical_status = "CERTIFIED";
    answer.mu_lo = lo; answer.mu_hi = hi;
    answer.lower_certificate = low; answer.upper_certificate = high;
    answer.reason = reason; answer.bisection_termination = reason;
    answer.queries = count; answer.validity_conditions = low.validity_conditions;
    if (!low.problem || !high.problem) return answer;
    const auto zero = build_limit_problem2(contacts, loads, Rational(0));
    const auto one = build_limit_problem2(contacts, loads, Rational(1));
    const auto matrix = affine_matrix2(zero, one);
    const auto lower = mechanism_basis2(low, matrix), upper = improving_basis2(high, matrix);
    if (lower) answer.critical_polynomials.push_back(*lower);
    if (upper) answer.critical_polynomials.push_back(*upper);
    Vector candidates;
    for (const auto& candidate : Vector{lo, hi, rational_candidate2(lo, hi)})
        if (std::find(candidates.begin(), candidates.end(), candidate) == candidates.end()) candidates.push_back(candidate);
    for (const auto& candidate : candidates) {
        if (!candidate_is_boundary2(candidate, lower, upper)) continue;
        const auto at = limit_load_ideal_exact_2d(contacts, loads, candidate, options);
        ++count;
        const auto below = branch_signs2(lower, lo, candidate), above = branch_signs2(upper, candidate, hi);
        const bool closed = at.mathematical_status == "UNBOUNDED" && (candidate == Rational(0) || below.has_value());
        const bool opened = at.mathematical_status == "OPTIMAL" && !nonzero(zero.b) && above && candidate < hi;
        if (!closed && !opened) continue;
        answer.attained = closed;
        answer.exact_threshold = candidate;
        answer.threshold_certificate = at;
        answer.threshold_proof = ThresholdProof2{candidate, closed, lower, upper, {lo, candidate}, {candidate, hi}, below, above};
        answer.threshold_proof_reason = "exact_basis_continuation";
        answer.queries = count;
        return answer;
    }
    answer.queries = count;
    return answer;
}
} // namespace

CriticalParameter2 critical_parameter(const contact::ContactSet2& contacts, const Loads2& loads,
    const Rational& mu_max, std::size_t max_steps, const std::string& param, const opt::Options& options) {
    geometry2::GeometryWorkScope work(contacts.assembly.limits);
    exact::IntegerLimitScope integers(contacts.assembly.limits.max_integer_bits);
    CriticalParameter2 answer;
    if (param != "mu") { answer.call_status = "UNSUPPORTED"; answer.reason = "only_mu_is_monotone"; return answer; }
    if (mu_max < Rational(0) || !critical_detail::is_binary64(mu_max)) {
        answer.call_status = "INVALID_INPUT"; answer.reason = "invalid search domain"; return answer;
    }
    auto low = limit_load_ideal_exact_2d(contacts, loads, Rational(0), options);
    answer.queries = 1;
    answer.validity_conditions = low.validity_conditions;
    if (low.mathematical_status == "UNBOUNDED") {
        answer.mathematical_status = "CERTIFIED";
        answer.mu_lo = Rational(0); answer.mu_hi = Rational(0); answer.attained = true;
        answer.upper_certificate = low; answer.threshold_certificate = low; answer.exact_threshold = Rational(0);
        return answer;
    }
    if (low.mathematical_status != "OPTIMAL" && low.mathematical_status != "INFEASIBLE") {
        answer.call_status = low.call_status; answer.reason = low.reason.value_or("lower_certificate_unavailable"); return answer;
    }
    auto high = mu_max == Rational(0) ? low : limit_load_ideal_exact_2d(contacts, loads, mu_max, options);
    std::size_t count = mu_max == Rational(0) ? 1 : 2;
    answer.queries = count;
    answer.validity_conditions = high.validity_conditions;
    if (high.mathematical_status == "INFEASIBLE" || high.mathematical_status == "OPTIMAL") {
        answer.mathematical_status = high.mathematical_status == "INFEASIBLE" ? "INFEASIBLE" : "CERTIFIED";
        answer.mu_lo = mu_max; answer.lower_certificate = high;
        answer.reason = high.mathematical_status == "INFEASIBLE" ? "infeasible_on_domain" : "bounded_on_domain";
        return answer;
    }
    if (high.mathematical_status != "UNBOUNDED") {
        answer.call_status = high.call_status; answer.reason = high.reason.value_or("upper_certificate_unavailable"); return answer;
    }
    Rational lo(0), hi = mu_max;
    for (std::size_t step = 0; step < max_steps; ++step) {
        const auto mid = critical_detail::binary_midpoint(lo, hi);
        if (!mid) return finish_critical(contacts, loads, lo, hi, low, high, "input_resolution_limit", count, options);
        const auto probe = limit_load_ideal_exact_2d(contacts, loads, *mid, options);
        ++count;
        if (probe.mathematical_status == "UNBOUNDED") { hi = *mid; high = probe; }
        else if (probe.mathematical_status == "OPTIMAL" || probe.mathematical_status == "INFEASIBLE") { lo = *mid; low = probe; }
        else {
            answer.call_status = probe.call_status; answer.reason = "query_certificate_unavailable";
            answer.mu_lo = lo; answer.mu_hi = hi; answer.lower_certificate = low; answer.upper_certificate = high;
            answer.queries = count; answer.validity_conditions = low.validity_conditions;
            return answer;
        }
    }
    const auto reason = critical_detail::binary_midpoint(lo, hi) ? "iteration_limit" : "input_resolution_limit";
    return finish_critical(contacts, loads, lo, hi, low, high, reason, count, options);
}

namespace {
std::string quote(const std::string& text) {
    static const char hex[] = "0123456789abcdef";
    std::string out = "\"";
    for (const unsigned char c : text) {
        if (c == '\\' || c == '"') { out += '\\'; out += static_cast<char>(c); }
        else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
        else out += static_cast<char>(c);
    }
    return out + '"';
}
template <class Range, class F> std::string array_json(const Range& range, F f) {
    std::string out = "[";
    bool first = true;
    for (const auto& value : range) { if (!first) out += ','; first = false; out += f(value); }
    return out + ']';
}
std::string js(const Rational& q) { return quote(q.canonical()); }
std::string js(const std::string& value) { return quote(value); }
std::string js(bool value) { return value ? "true" : "false"; }
std::string js(std::size_t value) { return std::to_string(value); }
template <class T> std::string optional_json(const std::optional<T>& value) { return value ? js(*value) : "null"; }
std::string vector_json(const Vector& v) { return array_json(v, [](const auto& q) { return js(q); }); }
std::string basis_json(const CriticalBasis2& b) {
    return "{\"kind\":" + quote(b.kind) + ",\"basis\":" + array_json(b.basis, [](auto i) { return js(i); }) +
        ",\"entering\":" + optional_json(b.entering) + ",\"determinant\":" + vector_json(b.determinant) +
        ",\"numerators\":" + array_json(b.numerators, vector_json) + ",\"labels\":" +
        array_json(b.labels, [](const auto& label) { return export_exact(label); }) +
        ",\"sample_parameter\":" + js(b.sample_parameter) + ",\"sample_values\":" + vector_json(b.sample_values) + '}';
}
std::string signs_json(const BranchSigns2& signs) {
    return array_json(signs, [](const BranchSign2& s) {
        return '[' + (s.index ? js(*s.index) : quote("denominator")) + ',' +
            array_json(s.endpoint_orders, [](auto n) { return js(n); }) + ',' + js(s.value) + ']';
    });
}
std::string proof_json(const ThresholdProof2& p) {
    return "{\"exact_threshold\":" + js(p.exact_threshold) + ",\"attained\":" + js(p.attained) +
        ",\"lower_basis\":" + (p.lower_basis ? basis_json(*p.lower_basis) : "null") +
        ",\"upper_basis\":" + (p.upper_basis ? basis_json(*p.upper_basis) : "null") +
        ",\"lower_interval\":" + array_json(p.lower_interval, [](const auto& q) { return js(q); }) +
        ",\"upper_interval\":" + array_json(p.upper_interval, [](const auto& q) { return js(q); }) +
        ",\"lower_signs\":" + (p.lower_signs ? signs_json(*p.lower_signs) : "null") +
        ",\"upper_signs\":" + (p.upper_signs ? signs_json(*p.upper_signs) : "null") +
        ",\"reason\":" + quote(p.reason) + '}';
}
std::string bits_json(const std::optional<Rational>& q) {
    if (!q) return "null";
    if (!critical_detail::is_binary64(*q)) throw std::logic_error("nonbinary64 critical bracket endpoint");
    std::ostringstream out;
    out << '"' << std::hex << std::setfill('0') << std::setw(16) << numeric::scalar_rational(*q, true) << '"';
    return out.str();
}
} // namespace
std::string export_exact(const CriticalParameter2& r) {
    return "{\"call_status\":" + quote(r.call_status) + ",\"mathematical_status\":" + quote(r.mathematical_status) +
        ",\"mu_lo\":" + optional_json(r.mu_lo) + ",\"mu_hi\":" + optional_json(r.mu_hi) +
        ",\"mu_lo_bits\":" + bits_json(r.mu_lo) + ",\"mu_hi_bits\":" + bits_json(r.mu_hi) +
        ",\"attained\":" + optional_json(r.attained) +
        ",\"lower_certificate\":" + (r.lower_certificate ? export_exact(*r.lower_certificate) : "null") +
        ",\"upper_certificate\":" + (r.upper_certificate ? export_exact(*r.upper_certificate) : "null") +
        ",\"reason\":" + optional_json(r.reason) + ",\"exact_threshold\":" + optional_json(r.exact_threshold) +
        ",\"critical_polynomials\":" + array_json(r.critical_polynomials, basis_json) +
        ",\"queries\":" + js(r.queries) +
        ",\"threshold_certificate\":" + (r.threshold_certificate ? export_exact(*r.threshold_certificate) : "null") +
        ",\"threshold_proof\":" + (r.threshold_proof ? proof_json(*r.threshold_proof) : "null") +
        ",\"bisection_termination\":" + optional_json(r.bisection_termination) +
        ",\"threshold_proof_reason\":" + optional_json(r.threshold_proof_reason) +
        ",\"validity_conditions\":" + array_json(r.validity_conditions, [](const auto& s) { return quote(s); }) + '}';
}
} // namespace eab2::statics
