#include "opt.hpp"
#include <algorithm>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace eab2::opt {
namespace {
void validate(const Matrix& A, const Vector& b, const Vector& c) {
    if (A.size() != b.size()) throw std::invalid_argument("LP row/right-hand-side dimension mismatch");
    if (c.size() > std::numeric_limits<std::size_t>::max() - A.size())
        throw exact::ResourceLimit("LP combined dimension overflow");
    for (const auto& row : A)
        if (row.size() != c.size()) throw std::invalid_argument("LP coefficient/objective dimension mismatch");
}
Rational dot(const Vector& a, const Vector& b) {
    Rational result;
    for (std::size_t i = 0; i < a.size(); ++i)
        if (a[i].sign() && b[i].sign()) result = result + a[i] * b[i];
    return result;
}
void observe(Statistics& stats, const Rational& value) {
    stats.max_stored_integer_bits = std::max({stats.max_stored_integer_bits,
        value.numerator().bit_length(), value.denominator().bit_length()});
}
void observe(Statistics& stats, const Vector& values) {
    for (const auto& value : values) observe(stats, value);
}
void observe(Statistics& stats, const Matrix& values) {
    for (const auto& row : values) observe(stats, row);
}
bool nonnegative(const Vector& values) {
    return std::all_of(values.begin(), values.end(), [](const auto& v) { return v.sign() >= 0; });
}
struct Model {
    std::size_t m, n;
    Matrix A;
    Vector b, c;
    std::vector<bool> flipped;

    Model(const Matrix& input, const Vector& rhs, const Vector& cost)
        : m(input.size()), n(cost.size()), A(input), b(rhs), c(cost), flipped(m) {
        for (std::size_t i = 0; i < m; ++i) {
            flipped[i] = b[i].sign() < 0;
            if (flipped[i]) {
                for (auto& value : A[i]) value = -value;
                b[i] = -b[i];
            }
        }
    }
    Vector column(std::size_t j) const {
        Vector result(m);
        if (j < n) {
            for (std::size_t i = 0; i < m; ++i) result[i] = A[i][j];
        } else result[j - n] = Rational(1);
        return result;
    }
    bool valid_basis(const std::vector<std::size_t>& basis) const {
        if (basis.size() != m) return false;
        auto sorted = basis;
        std::sort(sorted.begin(), sorted.end());
        return (sorted.empty() || sorted.back() < n + m) &&
            std::adjacent_find(sorted.begin(), sorted.end()) == sorted.end();
    }
    std::optional<Matrix> inverse(const std::vector<std::size_t>& basis) const {
        if (!valid_basis(basis)) return std::nullopt;
        Matrix left(m, Vector(m)), right(m, Vector(m));
        for (std::size_t j = 0; j < m; ++j) {
            const auto col = column(basis[j]);
            for (std::size_t i = 0; i < m; ++i) left[i][j] = col[i];
            right[j][j] = Rational(1);
        }
        for (std::size_t j = 0; j < m; ++j) {
            auto pivot = j;
            while (pivot < m && !left[pivot][j].sign()) ++pivot;
            if (pivot == m) return std::nullopt;
            std::swap(left[j], left[pivot]);
            std::swap(right[j], right[pivot]);
            const auto value = left[j][j];
            for (std::size_t k = 0; k < m; ++k) {
                left[j][k] = left[j][k] / value;
                right[j][k] = right[j][k] / value;
            }
            for (std::size_t i = 0; i < m; ++i) {
                if (i == j || !left[i][j].sign()) continue;
                const auto factor = left[i][j];
                for (std::size_t k = 0; k < m; ++k) {
                    left[i][k] = left[i][k] - factor * left[j][k];
                    right[i][k] = right[i][k] - factor * right[j][k];
                }
            }
        }
        return right;
    }
    Vector basic_values(const Matrix& inverse) const {
        Vector result;
        result.reserve(m);
        for (const auto& row : inverse) result.push_back(dot(row, b));
        return result;
    }
    Vector dual(const Matrix& inverse, const std::vector<std::size_t>& basis,
                const Vector& cost) const {
        Vector y(m);
        for (std::size_t i = 0; i < m; ++i)
            if (cost[basis[i]].sign())
                for (std::size_t k = 0; k < m; ++k)
                    y[k] = y[k] + cost[basis[i]] * inverse[i][k];
        return y;
    }
    Vector original_dual(Vector y) const {
        for (std::size_t i = 0; i < m; ++i) if (flipped[i]) y[i] = -y[i];
        return y;
    }
};

std::optional<Result> certify(const Model& model, const Candidate& candidate) {
    auto inverse = model.inverse(candidate.basis);
    if (!inverse) return std::nullopt;
    const auto m = model.m, n = model.n;
    Result result;
    result.status = candidate.status;
    result.basis = candidate.basis;
    observe(result.stats, *inverse);
    if (candidate.status == Status::infeasible) {
        Vector phase1(n + m);
        for (std::size_t i = n; i < n + m; ++i) phase1[i] = Rational(1);
        const auto y = model.dual(*inverse, candidate.basis, phase1);
        if (dot(y, model.b).sign() <= 0) return std::nullopt;
        for (std::size_t j = 0; j < n; ++j)
            if (dot(y, model.column(j)).sign() > 0) return std::nullopt;
        result.exact_y = model.original_dual(y);
        return result;
    }
    const auto basic = model.basic_values(*inverse);
    for (std::size_t i = 0; i < m; ++i)
        if (basic[i].sign() < 0 || (candidate.basis[i] >= n && basic[i].sign()))
            return std::nullopt;
    result.exact_x.resize(n);
    for (std::size_t i = 0; i < m; ++i)
        if (candidate.basis[i] < n) result.exact_x[candidate.basis[i]] = basic[i];
    Vector cost = model.c;
    cost.resize(n + m);
    const auto y = model.dual(*inverse, candidate.basis, cost);
    if (candidate.status == Status::unbounded) {
        if (!candidate.entering || *candidate.entering >= n ||
            std::find(candidate.basis.begin(), candidate.basis.end(), *candidate.entering) != candidate.basis.end())
            return std::nullopt;
        const auto entering = *candidate.entering;
        const auto column = model.column(entering);
        Vector direction;
        for (const auto& row : *inverse) direction.push_back(dot(row, column));
        for (std::size_t i = 0; i < m; ++i)
            if (direction[i].sign() > 0 || (candidate.basis[i] >= n && direction[i].sign()))
                return std::nullopt;
        const auto improvement = model.c[entering] - dot(y, column);
        if (improvement.sign() >= 0) return std::nullopt;
        result.exact_ray.resize(n);
        result.exact_ray[entering] = Rational(1) / -improvement;
        for (std::size_t i = 0; i < m; ++i)
            if (candidate.basis[i] < n) result.exact_ray[candidate.basis[i]] = direction[i] / improvement;
        return result;
    }
    if (candidate.status != Status::optimal) return std::nullopt;
    for (std::size_t j = 0; j < n; ++j)
        if ((model.c[j] - dot(y, model.column(j))).sign() < 0) return std::nullopt;
    result.exact_y = model.original_dual(y);
    result.exact_objective = dot(model.c, result.exact_x);
    return result;
}

struct Simplex {
    const Model& model;
    const Options& options;
    Statistics& stats;
    Matrix inverse;
    Vector basic;
    std::vector<std::size_t> basis;

    Vector direction(std::size_t entering) const {
        const auto column = model.column(entering);
        Vector result;
        for (const auto& row : inverse) result.push_back(dot(row, column));
        return result;
    }
    void pivot(std::size_t leave, std::size_t entering, const Vector& d, const Rational& theta) {
        if (stats.pivots >= options.max_pivots)
            throw exact::ResourceLimit("exact LP pivot work limit exceeded; no answer returned");
        Vector row = inverse[leave];
        for (auto& value : row) value = value / d[leave];
        for (std::size_t i = 0; i < model.m; ++i) {
            if (i == leave || !d[i].sign()) continue;
            for (std::size_t k = 0; k < model.m; ++k)
                inverse[i][k] = inverse[i][k] - d[i] * row[k];
            basic[i] = basic[i] - theta * d[i];
        }
        inverse[leave] = std::move(row);
        basic[leave] = theta;
        basis[leave] = entering;
        ++stats.pivots;
        observe(stats, inverse);
        observe(stats, basic);
    }
    Candidate run(const Vector& cost, std::size_t allowed, bool phase2) {
        std::size_t degenerate = 0;
        bool bland = false;
        for (;;) {
            const auto y = model.dual(inverse, basis, cost);
            observe(stats, y);
            std::vector<bool> in_basis(model.n + model.m);
            for (const auto j : basis) in_basis[j] = true;
            std::optional<std::size_t> entering;
            Rational best;
            for (std::size_t j = 0; j < allowed; ++j) {
                if (in_basis[j]) continue;
                const auto reduced = cost[j] - dot(y, model.column(j));
                observe(stats, reduced);
                if (reduced.sign() < 0 && (!entering || reduced < best)) {
                    entering = j;
                    best = reduced;
                    if (bland) break;
                }
            }
            if (!entering) return {Status::optimal, basis, std::nullopt};
            const auto d = direction(*entering);
            observe(stats, d);
            std::optional<std::size_t> leave;
            Rational theta;
            for (std::size_t i = 0; i < model.m; ++i) {
                Rational ratio;
                if (phase2 && basis[i] >= model.n && d[i].sign()) {
                    // A redundant artificial variable must stay identically zero.
                    ratio = Rational(0);
                } else if (d[i].sign() > 0) ratio = basic[i] / d[i];
                else continue;
                if (!leave || ratio < theta || (ratio == theta && basis[i] < basis[*leave])) {
                    leave = i;
                    theta = ratio;
                }
            }
            if (!leave) return {Status::unbounded, basis, entering};
            degenerate = theta.sign() ? 0 : degenerate + 1;
            if (degenerate > 2 * model.m + 10) {
                bland = true;
                stats.bland_used = true;
            }
            pivot(*leave, *entering, d, theta);
        }
    }
    Candidate execute(const std::optional<Candidate>& hint) {
        const auto m = model.m, n = model.n;
        bool warm = false;
        if (hint) {
            auto proposed = model.inverse(hint->basis);
            if (proposed) {
                auto values = model.basic_values(*proposed);
                warm = nonnegative(values);
                for (std::size_t i = 0; i < m && warm; ++i)
                    if (hint->basis[i] >= n && values[i].sign()) warm = false;
                if (warm) {
                    inverse = std::move(*proposed);
                    basic = std::move(values);
                    basis = hint->basis;
                    stats.candidate_warm_started = true;
                }
            }
        }
        if (!warm) {
            inverse.assign(m, Vector(m));
            basis.resize(m);
            for (std::size_t i = 0; i < m; ++i) {
                inverse[i][i] = Rational(1);
                basis[i] = n + i;
            }
            basic = model.b;
            Vector cost(n + m);
            for (std::size_t i = n; i < n + m; ++i) cost[i] = Rational(1);
            if (run(cost, n + m, false).status != Status::optimal)
                throw std::logic_error("exact LP phase one cannot be unbounded");
            for (std::size_t i = 0; i < m; ++i)
                if (basis[i] >= n && basic[i].sign())
                    return {Status::infeasible, basis, std::nullopt};
        }
        // Zero-valued artificial columns are pivoted out whenever possible.
        for (std::size_t i = 0; i < m; ++i) {
            if (basis[i] < n) continue;
            for (std::size_t j = 0; j < n; ++j) {
                if (std::find(basis.begin(), basis.end(), j) != basis.end()) continue;
                const auto d = direction(j);
                if (d[i].sign()) {
                    pivot(i, j, d, Rational(0));
                    break;
                }
            }
        }
        basic = model.basic_values(inverse);
        Vector cost = model.c;
        cost.resize(n + m);
        return run(cost, n, true);
    }
};

Result solve_core(const Matrix& A, const Vector& b, const Vector& c,
                  const Options& options, Statistics& stats, bool allow_hint) {
    const Model model(A, b, c);
    observe(stats, A);
    observe(stats, b);
    observe(stats, c);
    if (allow_hint && options.candidate) {
        auto answer = certify(model, *options.candidate);
        if (answer) {
            stats.candidate_accepted = true;
            stats.max_stored_integer_bits = std::max(stats.max_stored_integer_bits,
                                                    answer->stats.max_stored_integer_bits);
            return *answer;
        }
    }
    Simplex simplex{model, options, stats, {}, {}, {}};
    const auto candidate = simplex.execute(allow_hint ? options.candidate : std::nullopt);
    auto answer = certify(model, candidate);
    if (!answer) throw std::logic_error("exact simplex failed exact basis certificate");
    stats.max_stored_integer_bits = std::max(stats.max_stored_integer_bits,
                                            answer->stats.max_stored_integer_bits);
    return *answer;
}
} // namespace

const char* status_name(Status status) {
    switch (status) {
        case Status::optimal: return "optimal";
        case Status::infeasible: return "infeasible";
        case Status::unbounded: return "unbounded";
    }
    throw std::invalid_argument("invalid LP status");
}

bool verify_certificate(const Matrix& A, const Vector& b, const Vector& c,
                        const Result& result, bool maximize_objective) {
    validate(A, b, c);
    const auto m = A.size(), n = c.size();
    if (result.status == Status::infeasible) {
        if (result.exact_y.size() != m || result.exact_objective || !result.exact_x.empty() || !result.exact_ray.empty())
            return false;
        if (dot(result.exact_y, b).sign() <= 0) return false;
        for (std::size_t j = 0; j < n; ++j) {
            Rational value;
            for (std::size_t i = 0; i < m; ++i) value = value + result.exact_y[i] * A[i][j];
            if (value.sign() > 0) return false;
        }
        return true;
    }
    if (result.exact_x.size() != n || !nonnegative(result.exact_x)) return false;
    for (std::size_t i = 0; i < m; ++i)
        if (dot(A[i], result.exact_x) != b[i]) return false;
    if (result.status == Status::unbounded) {
        if (result.exact_ray.size() != n || !nonnegative(result.exact_ray) || result.exact_objective || !result.exact_y.empty())
            return false;
        for (const auto& row : A) if (dot(row, result.exact_ray).sign()) return false;
        return dot(c, result.exact_ray) == Rational(maximize_objective ? 1 : -1);
    }
    if (result.status != Status::optimal || result.exact_y.size() != m || !result.exact_objective || !result.exact_ray.empty())
        return false;
    for (std::size_t j = 0; j < n; ++j) {
        Rational dual_column;
        for (std::size_t i = 0; i < m; ++i) dual_column = dual_column + result.exact_y[i] * A[i][j];
        if (maximize_objective ? dual_column < c[j] : dual_column > c[j]) return false;
    }
    return dot(c, result.exact_x) == *result.exact_objective && dot(b, result.exact_y) == *result.exact_objective;
}

std::optional<Result> certify_candidate(const Matrix& A, const Vector& b,
                                        const Vector& c, const Candidate& candidate) {
    validate(A, b, c);
    auto result = certify(Model(A, b, c), candidate);
    if (result && !verify_certificate(A, b, c, *result))
        throw std::logic_error("basis certificate disagrees with original LP");
    return result;
}

Result solve(const Matrix& A, const Vector& b, const Vector& c, const Options& options) {
    validate(A, b, c);
    Statistics stats;
    auto answer = solve_core(A, b, c, options, stats, true);
    if (answer.status == Status::unbounded) {
        // Design 4.6.1: obtain both public witnesses from auxiliary exact LPs,
        // never from rounded display values or a self-stress explanation.
        const Vector zero_cost(c.size());
        ++stats.auxiliary_solves;
        const auto point = solve_core(A, b, zero_cost, options, stats, false);
        Matrix ray_A = A;
        ray_A.push_back(c);
        Vector ray_b(A.size());
        ray_b.emplace_back(-1);
        ++stats.auxiliary_solves;
        const auto ray = solve_core(ray_A, ray_b, zero_cost, options, stats, false);
        if (point.status != Status::optimal || ray.status != Status::optimal)
            throw std::logic_error("unbounded LP auxiliary witnesses unavailable");
        answer.exact_x = point.exact_x;
        answer.exact_ray = ray.exact_x;
    }
    if (!verify_certificate(A, b, c, answer)) throw std::logic_error("LP result failed original-model certificate");
    observe(stats, answer.exact_x);
    observe(stats, answer.exact_y);
    observe(stats, answer.exact_ray);
    if (answer.exact_objective) observe(stats, *answer.exact_objective);
    answer.stats = stats;
    return answer;
}

Result maximize(const Matrix& A, const Vector& b, const Vector& c, const Options& options) {
    Vector negative = c;
    for (auto& value : negative) value = -value;
    auto result = solve(A, b, negative, options);
    if (result.status == Status::optimal) {
        result.exact_objective = -*result.exact_objective;
        for (auto& value : result.exact_y) value = -value;
    }
    if (!verify_certificate(A, b, c, result, true)) throw std::logic_error("max LP sign mapping failed certificate");
    return result;
}

Result homogeneous_feasibility(const Matrix& A, const Vector& normalizer, const Options& options) {
    Matrix normalized = A;
    normalized.push_back(normalizer);
    Vector rhs(A.size());
    rhs.emplace_back(1);
    return solve(normalized, rhs, Vector(normalizer.size()), options);
}

std::string export_exact(const Result& result, bool maximize_objective) {
    std::ostringstream out;
    const auto vector = [&](const Vector& values) {
        out << '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
            if (i) out << ',';
            out << '"' << values[i].canonical() << '"';
        }
        out << ']';
    };
    out << "{\"status\":\"" << status_name(result.status) << "\",\"sense\":\""
        << (maximize_objective ? "max" : "min") << "\",\"objective\":";
    if (result.exact_objective) out << '"' << result.exact_objective->canonical() << '"';
    else out << "null";
    out << ",\"x\":";
    vector(result.exact_x);
    out << ",\"y\":";
    vector(result.exact_y);
    out << ",\"ray\":";
    vector(result.exact_ray);
    out << ",\"basis\":[";
    for (std::size_t i = 0; i < result.basis.size(); ++i) {
        if (i) out << ',';
        out << result.basis[i];
    }
    out << "],\"pivots\":" << result.stats.pivots
        << ",\"auxiliary_solves\":" << result.stats.auxiliary_solves
        << ",\"max_stored_integer_bits\":" << result.stats.max_stored_integer_bits
        << ",\"candidate_accepted\":" << (result.stats.candidate_accepted ? "true" : "false")
        << ",\"candidate_warm_started\":" << (result.stats.candidate_warm_started ? "true" : "false")
        << ",\"bland_used\":" << (result.stats.bland_used ? "true" : "false") << '}';
    return out.str();
}
} // namespace eab2::opt
