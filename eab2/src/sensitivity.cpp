#if defined(__AVX__)
#error eab2 controlled sources require the x64 SSE2 compilation target
#endif
#include "sensitivity.hpp"
#include "branch.hpp"
#include "geometry_seed.hpp"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <type_traits>

namespace eab2::statics {
namespace {
Rational dot(const Vector& a, const Vector& b) {
    if (a.size() != b.size()) throw std::logic_error("sensitivity vector width mismatch");
    Rational value;
    for (std::size_t i = 0; i < a.size(); ++i) value = value + a[i] * b[i];
    return value;
}
bool nonzero(const Vector& a) {
    return std::any_of(a.begin(), a.end(), [](const Rational& x) { return x != Rational(0); });
}
std::size_t checked_width(std::size_t a, std::size_t factor, std::size_t extra) {
    if (a > (std::numeric_limits<std::size_t>::max() - extra) / factor)
        throw exact::ResourceLimit("sensitivity dimension overflow");
    return factor * a + extra;
}
void check_matrix(std::size_t rows, std::size_t columns) {
    geometry2::GeometryWorkScope work;
    work.check_size(rows); work.check_size(columns);
    if (columns && rows > work.limits.max_elements / columns)
        throw exact::ResourceLimit("sensitivity matrix element limit");
}
std::optional<Matrix> inverse(const Matrix& matrix) {
    const auto n = matrix.size();
    const auto width = checked_width(n, 2, 0);
    check_matrix(n, width);
    Matrix work(n, Vector(width));
    for (std::size_t i = 0; i < n; ++i) {
        if (matrix[i].size() != n) return std::nullopt;
        std::copy(matrix[i].begin(), matrix[i].end(), work[i].begin());
        work[i][n + i] = Rational(1);
    }
    for (std::size_t j = 0; j < n; ++j) {
        auto pivot = j;
        while (pivot < n && work[pivot][j] == Rational(0)) ++pivot;
        if (pivot == n) return std::nullopt;
        std::swap(work[j], work[pivot]);
        const auto scale = work[j][j];
        for (auto& value : work[j]) value = value / scale;
        for (std::size_t i = 0; i < n; ++i) if (i != j && work[i][j] != Rational(0)) {
            const auto factor = work[i][j];
            for (std::size_t k = 0; k < 2 * n; ++k)
                work[i][k] = work[i][k] - factor * work[j][k];
        }
    }
    Matrix out;
    for (const auto& row : work) out.emplace_back(row.begin() + static_cast<std::ptrdiff_t>(n), row.end());
    return out;
}
std::optional<Vector> null_vector(Matrix work, std::size_t n) {
    std::vector<std::size_t> pivots;
    for (const auto& row : work) if (row.size() != n) throw std::logic_error("null-space matrix width");
    for (std::size_t j = 0; j < n; ++j) {
        auto pivot = pivots.size();
        while (pivot < work.size() && work[pivot][j] == Rational(0)) ++pivot;
        if (pivot == work.size()) continue;
        const auto row = pivots.size();
        std::swap(work[row], work[pivot]);
        const auto scale = work[row][j];
        for (auto& value : work[row]) value = value / scale;
        for (std::size_t i = 0; i < work.size(); ++i) if (i != row && work[i][j] != Rational(0)) {
            const auto factor = work[i][j];
            for (std::size_t k = 0; k < n; ++k) work[i][k] = work[i][k] - factor * work[row][k];
        }
        pivots.push_back(j);
    }
    std::size_t free = 0;
    while (free < n && std::find(pivots.begin(), pivots.end(), free) != pivots.end()) ++free;
    if (free == n) return std::nullopt;
    Vector ray(n);
    ray[free] = Rational(1);
    for (std::size_t i = 0; i < pivots.size(); ++i) ray[pivots[i]] = -work[i][free];
    return ray;
}
void append_unique(std::vector<std::string>& values, const std::string& value) {
    if (std::find(values.begin(), values.end(), value) == values.end()) values.push_back(value);
}
std::string quote(const std::string& value) {
    std::string out = "\"";
    const char* hex = "0123456789abcdef";
    for (const unsigned char ch : value) {
        if (ch == '\\' || ch == '"') { out += '\\'; out += static_cast<char>(ch); }
        else if (ch < 32) { out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15]; }
        else out += static_cast<char>(ch);
    }
    return out + '"';
}
template<class Range, class Encode> std::string array(const Range& values, Encode encode) {
    std::string out = "[";
    bool first = true;
    for (const auto& value : values) { if (!first) out += ','; first = false; out += encode(value); }
    return out + ']';
}
std::string rational(const Rational& value) { return quote(value.canonical()); }
std::string vector(const Vector& values) { return array(values, rational); }
std::string indices(const std::vector<std::size_t>& values) {
    return array(values, [](std::size_t value) { return std::to_string(value); });
}
std::string label(const SensitivityLabel2& value) {
    return std::visit([](const auto& item) {
        if constexpr (std::is_same_v<std::decay_t<decltype(item)>, std::string>) return quote(item);
        else return export_exact(item);
    }, value);
}
std::string piece_label(const SensitivityPieceLabel2& value) {
    return std::visit([](const auto& item) {
        using T = std::decay_t<decltype(item)>;
        if constexpr (std::is_same_v<T, std::string>) return quote(item);
        else if constexpr (std::is_same_v<T, std::vector<std::size_t>>) return indices(item);
        else return export_exact(item);
    }, value);
}
void append_unique(std::vector<SensitivityLabel2>& values, const SensitivityLabel2& value) {
    const auto encoded = label(value);
    if (std::none_of(values.begin(), values.end(), [&](const auto& present) { return label(present) == encoded; }))
        values.push_back(value);
}
SensitivityResult2 initial(const std::optional<std::string>& status, const std::vector<std::string>& conditions,
                           const SensitivityOptions2& options) {
    SensitivityResult2 out;
    out.mathematical_status = status;
    out.parameter = options.parameter;
    out.tied_labels = options.tied_labels;
    out.validity_conditions = {"L1接触骨架不变"};
    for (const auto& value : options.validity_conditions) append_unique(out.validity_conditions, value);
    for (const auto& value : conditions) append_unique(out.validity_conditions, value);
    return out;
}
bool valid_seed(const LimitProblem2& problem, const LimitSeed2& seed) {
    const auto m = problem.b.size(), n = problem.c.size();
    return seed.dA.size() == m && seed.db.size() == m && seed.dc.size() == n &&
        std::all_of(seed.dA.begin(), seed.dA.end(), [&](const auto& row) { return row.size() == n; });
}
void check_model(const LimitProblem2& problem) {
    const auto m = problem.b.size(), n = problem.c.size();
    if (problem.A.size() != m || std::any_of(problem.A.begin(), problem.A.end(),
        [&](const auto& row) { return row.size() != n; })) throw std::logic_error("sensitivity model dimensions");
    geometry2::GeometryWorkScope work;
    work.check_size(m); work.check_size(n);
    if (m > (std::numeric_limits<std::size_t>::max() - 2) / 2 ||
        n > (std::numeric_limits<std::size_t>::max() - 2) / 2 ||
        (2 * m + 1) > work.limits.max_elements / (2 * n + 2))
        throw exact::ResourceLimit("sensitivity auxiliary matrix element limit");
}
void verify_optimum(const LimitResult2& result) {
    if (!result.problem || !result.exact_x || !result.exact_y || !result.exact_value)
        throw std::logic_error("finite sensitivity requires original exact certificate");
    const auto& p = *result.problem;
    opt::Result witness;
    witness.status = opt::Status::optimal;
    witness.exact_x = *result.exact_x; witness.exact_y = *result.exact_y; witness.exact_objective = result.exact_value;
    if (!opt::verify_certificate(p.A, p.b, p.c, witness, true))
        throw std::logic_error("sensitivity original optimum certificate failed");
}
LimitSeed2 unit_mu_seed(const LimitProblem2& problem) {
    const auto& assembly = problem.contact_set.assembly;
    const auto physical_columns = checked_width(problem.contact_set.constraints.size(), 2, 1);
    if (problem.c.size() != physical_columns || (assembly.bodies.empty() && !problem.A.empty()))
        throw std::invalid_argument("physical friction seed requires contact-column model");
    check_matrix(problem.A.size(), problem.c.size());
    LimitSeed2 seed{Matrix(problem.A.size(), Vector(problem.c.size())), Vector(problem.b.size()), Vector(problem.c.size()), "mu"};
    std::size_t column = 0;
    for (const auto& contact : problem.contact_set.constraints) for (const int sign : {-1, 1}) {
        const Point df{Rational(sign) * contact.tangent[0], Rational(sign) * contact.tangent[1]};
        std::size_t row = 0;
        for (std::size_t i = 0; i < assembly.bodies.size(); ++i) {
            const auto& body = assembly.bodies[i];
            if (body.boundary_type == "FIXED_BODY") continue;
            const Rational sense(static_cast<int>(i == contact.a) - static_cast<int>(i == contact.b));
            const auto arm = geometry2::sub(contact.point, body.dof_anchor);
            const Wrench wrench{sense * df[0], sense * df[1], sense * geometry2::cross(arm, df)};
            for (std::size_t k = 0; k < 3; ++k) if (body.dof_mask[k]) {
                if (row >= seed.dA.size()) throw std::logic_error("friction seed row mismatch");
                seed.dA[row++][column] = wrench[k];
            }
        }
        if (row != seed.dA.size()) throw std::logic_error("friction seed row count mismatch");
        ++column;
    }
    return seed;
}
bool stable(const LimitResult2& result) {
    const auto& p = *result.problem;
    const auto m = p.b.size(), n = p.c.size();
    const auto& basis = result.basis;
    if (basis.size() != m) return false;
    auto sorted = basis;
    std::sort(sorted.begin(), sorted.end());
    if (std::adjacent_find(sorted.begin(), sorted.end()) != sorted.end() ||
        (!sorted.empty() && sorted.back() >= n)) return false;
    Matrix B(m, Vector(m));
    for (std::size_t i = 0; i < m; ++i) for (std::size_t j = 0; j < m; ++j) B[i][j] = p.A[i][basis[j]];
    if (!inverse(B)) return false;
    for (const auto j : basis) if ((*result.exact_x)[j] <= Rational(0)) return false;
    for (std::size_t j = 0; j < n; ++j) if (std::find(basis.begin(), basis.end(), j) == basis.end()) {
        Rational cost;
        for (std::size_t i = 0; i < m; ++i) cost = cost + p.A[i][j] * (*result.exact_y)[i];
        if (cost == p.c[j]) return false;
    }
    return true;
}
std::optional<Vector> feasible(const Matrix& A, const Vector& b, std::size_t n, const opt::Options& options) {
    const Vector objective(n);
    const auto result = opt::solve(A, b, objective, options);
    if (!opt::verify_certificate(A, b, objective, result)) throw std::logic_error("recession feasibility certificate failed");
    if (result.status == opt::Status::infeasible) return std::nullopt;
    if (result.status != opt::Status::optimal) throw std::logic_error("zero objective is not finite");
    return result.exact_x;
}
std::pair<std::optional<Vector>, std::optional<Vector>> recession(const LimitProblem2& p, const opt::Options& options) {
    const auto m = p.b.size(), n = p.c.size();
    check_matrix(checked_width(m, 1, 2), n);
    Matrix primal_rows = p.A;
    primal_rows.push_back(p.c); primal_rows.emplace_back(n, Rational(1));
    Vector primal_rhs(m + 2); primal_rhs.back() = Rational(1);
    auto primal = feasible(primal_rows, primal_rhs, n, options);
    if (primal && (!nonzero(*primal) || dot(p.c, *primal) != Rational(0) ||
        std::any_of(primal->begin(), primal->end(), [](const auto& v) { return v < Rational(0); }) ||
        std::any_of(p.A.begin(), p.A.end(), [&](const auto& row) { return dot(row, *primal) != Rational(0); })))
        throw std::logic_error("primal recession verification failed");
    Matrix transposed(n, Vector(m));
    for (std::size_t i = 0; i < m; ++i) for (std::size_t j = 0; j < n; ++j) transposed[j][i] = p.A[i][j];
    auto dual = null_vector(transposed, m);
    if (!dual) {
        const auto width = checked_width(m, 2, n), row_count = checked_width(n, 1, 2);
        check_matrix(row_count, width);
        Matrix rows(row_count, Vector(width));
        for (std::size_t j = 0; j < n; ++j) {
            for (std::size_t i = 0; i < m; ++i) { rows[j][i] = transposed[j][i]; rows[j][m + i] = -transposed[j][i]; }
            rows[j][2 * m + j] = Rational(-1);
            rows[n + 1][2 * m + j] = Rational(1);
        }
        for (std::size_t i = 0; i < m; ++i) { rows[n][i] = p.b[i]; rows[n][m + i] = -p.b[i]; }
        Vector rhs(n + 2); rhs.back() = Rational(1);
        const auto witness = feasible(rows, rhs, width, options);
        if (witness) {
            Vector ray(m);
            for (std::size_t i = 0; i < m; ++i) ray[i] = (*witness)[i] - (*witness)[m + i];
            dual = std::move(ray);
        }
    }
    if (dual && (!nonzero(*dual) || dot(p.b, *dual) != Rational(0) ||
        std::any_of(transposed.begin(), transposed.end(), [&](const auto& row) { return dot(row, *dual) < Rational(0); })))
        throw std::logic_error("dual recession verification failed");
    return {std::move(primal), std::move(dual)};
}
struct Directional {
    Rational value;
    std::pair<Vector, Vector> certificate;
};
std::optional<Directional> mills(const LimitResult2& result, const LimitSeed2& seed, int sign,
                               const opt::Options& options) {
    const auto& p = *result.problem;
    const auto m = p.b.size(), n = p.c.size();
    const auto value = *result.exact_value;
    const auto row_count = checked_width(m, 2, 1), width = checked_width(n, 2, 2);
    check_matrix(row_count, width);
    Matrix rows(row_count, Vector(width));
    Vector rhs = p.b;
    rhs.push_back(value);
    for (const auto& v : seed.db) rhs.push_back(Rational(sign) * v);
    for (std::size_t i = 0; i < m; ++i) {
        for (std::size_t j = 0; j < n; ++j) {
            rows[i][j] = p.A[i][j];
            rows[m + 1 + i][j] = Rational(sign) * seed.dA[i][j];
            rows[m + 1 + i][n + j] = p.A[i][j];
        }
        rows[m + 1 + i][2 * n] = p.b[i]; rows[m + 1 + i][2 * n + 1] = -p.b[i];
    }
    Vector objective(2 * n + 2);
    for (std::size_t j = 0; j < n; ++j) {
        rows[m][j] = p.c[j];
        objective[j] = Rational(sign) * seed.dc[j]; objective[n + j] = p.c[j];
    }
    objective[2 * n] = value; objective[2 * n + 1] = -value;
    const auto answer = opt::maximize(rows, rhs, objective, options);
    if (!opt::verify_certificate(rows, rhs, objective, answer, true))
        throw std::logic_error("Mills/Freund original directional LP certificate failed");
    if (answer.status != opt::Status::optimal) return std::nullopt;
    return Directional{*answer.exact_objective, {answer.exact_x, answer.exact_y}};
}
Rational polynomial_value(const Polynomial2& p, const Rational& x) {
    Rational value;
    for (auto i = p.rbegin(); i != p.rend(); ++i) value = value * x + *i;
    return value;
}
int local_polynomial_sign(Polynomial2 p, const Rational& point, int side) {
    int parity = 1;
    while (nonzero(p)) {
        const auto value = polynomial_value(p, point);
        if (value != Rational(0)) return value.sign() * parity;
        Polynomial2 derivative;
        for (std::size_t k = 1; k < p.size(); ++k)
            derivative.push_back(Rational(exact::Int::decimal(std::to_string(k))) * p[k]);
        p = std::move(derivative); parity *= side;
    }
    return 0;
}
Vector basis_variation(const Matrix& A, const std::vector<std::size_t>& basis, const Matrix& inv,
                       const Vector& state, const LimitSeed2& seed, std::optional<std::size_t> entering, bool dual) {
    const auto m = A.size();
    Vector rhs(m), out(m);
    if (dual) {
        for (std::size_t k = 0; k < m; ++k) {
            rhs[k] = seed.dc[basis[k]];
            for (std::size_t i = 0; i < m; ++i) rhs[k] = rhs[k] - seed.dA[i][basis[k]] * state[i];
        }
        for (std::size_t i = 0; i < m; ++i) for (std::size_t k = 0; k < m; ++k) out[i] = out[i] + inv[k][i] * rhs[k];
    } else {
        if (!entering) throw std::logic_error("improving basis has no entering column");
        for (std::size_t i = 0; i < m; ++i) {
            rhs[i] = -seed.dA[i][*entering];
            for (std::size_t k = 0; k < m; ++k) rhs[i] = rhs[i] - seed.dA[i][basis[k]] * state[k];
        }
        for (std::size_t k = 0; k < m; ++k) for (std::size_t i = 0; i < m; ++i) out[k] = out[k] + inv[k][i] * rhs[i];
    }
    return out;
}
} // namespace

SensitivityResult2 evaluate_sensitivity2(const LimitResult2& result, const std::optional<LimitSeed2>& input,
                                        const SensitivityOptions2& options) {
    auto out = initial(result.mathematical_status, result.validity_conditions, options);
    out.call_status = result.call_status;
    if (result.call_status != "OK" || result.mathematical_status != "OPTIMAL") {
        out.reason = "finite_optimum_required";
        return out;
    }
    if (!result.problem) throw std::logic_error("finite sensitivity requires original exact problem");
    const auto& p = *result.problem;
    geometry2::GeometryWorkScope work(p.contact_set.assembly.limits);
    exact::IntegerLimitScope integers(p.contact_set.assembly.limits.max_integer_bits);
    check_model(p);
    verify_optimum(result);
    if (!input && options.parameter != "mu") {
        out.call_status = "UNSUPPORTED"; out.differentiability = "unsupported"; out.reason = "exact_seed_required";
        return out;
    }
    const auto seed = input ? *input : unit_mu_seed(p);
    if (!valid_seed(p, seed)) { out.call_status = "INVALID_INPUT"; out.reason = "seed_shape_mismatch"; return out; }
    if (!options.positive_direction_valid && !options.negative_direction_valid) { out.reason = "no_valid_direction"; return out; }
    if (stable(result)) {
        Vector rhs = seed.db;
        for (std::size_t i = 0; i < rhs.size(); ++i) rhs[i] = rhs[i] - dot(seed.dA[i], *result.exact_x);
        // L4 mutation target: original unscaled maximize dual, all three seeds.
        const auto derivative = dot(*result.exact_x, seed.dc) + dot(*result.exact_y, rhs);
        out.differentiability = options.positive_direction_valid && options.negative_direction_valid ? "smooth" : "one_sided";
        out.selected_piece = SensitivitySelectedPiece2{result.basis, std::nullopt, std::nullopt};
        out.display_status = "EXACT";
        if (options.positive_direction_valid) out.directional_derivative = out.right_derivative = derivative;
        if (options.negative_direction_valid) out.left_derivative = derivative;
        out.piece_jacobians.push_back({result.basis, derivative}); out.method = "stable_basis";
        return out;
    }
    auto rays = recession(p, options.lp_options);
    if (rays.first || rays.second) {
        out.differentiability = "singular"; out.reason = "possibly_discontinuous";
        out.primal_recession_ray = std::move(rays.first); out.dual_recession_ray = std::move(rays.second);
        out.method = "optimal_face_recession";
        return out;
    }
    const auto forward = options.positive_direction_valid ? mills(result, seed, 1, options.lp_options) : std::nullopt;
    const auto reverse = options.negative_direction_valid ? mills(result, seed, -1, options.lp_options) : std::nullopt;
    out.method = "mills_freund";
    if ((options.positive_direction_valid && !forward) || (options.negative_direction_valid && !reverse)) {
        out.reason = "directional_problem_not_finite";
        return out;
    }
    if (forward) { out.directional_derivative = out.right_derivative = forward->value; out.forward_certificate = forward->certificate; }
    // L4 mutation target: left-coordinate slope is MINUS the reverse LP value.
    if (reverse) { out.left_derivative = -reverse->value; out.reverse_certificate = reverse->certificate; }
    out.differentiability = out.right_derivative && out.left_derivative && out.right_derivative == out.left_derivative ? "smooth" : "one_sided";
    out.display_status = "EXACT";
    return out;
}

static SensitivityResult2 single_basis_candidate(const CriticalParameter2& critical, const std::optional<LimitSeed2>& input,
                                        const std::optional<LimitSeed2>& threshold_mu_seed, const SensitivityOptions2& options) {
    auto out = initial(critical.mathematical_status, critical.validity_conditions, options);
    if (critical.exact_threshold == Rational(0) && critical.attained.value_or(false) && !critical.threshold_proof) {
        out.reason = "threshold_on_domain_boundary_without_proof"; return out;
    }
    if (!critical.exact_threshold || !critical.threshold_certificate || !critical.threshold_proof || !input ||
        !critical.threshold_certificate->problem) {
        out.reason = "exact_threshold_basis_and_seed_required"; return out;
    }
    if (!options.positive_direction_valid && !options.negative_direction_valid) { out.reason = "no_valid_direction"; return out; }
    const auto& proof = *critical.threshold_proof;
    const auto point = *critical.exact_threshold;
    const bool attained = critical.attained.value_or(false);
    // L4 mutation target: an open threshold differentiates its MECHANISM basis,
    // never a diverging primal force or an upper-side improving-ray basis.
    const auto& selected = attained ? proof.upper_basis : proof.lower_basis;
    if (!selected) { out.reason = "critical_basis_unavailable"; return out; }
    const auto& branch = *selected;
    const auto& p = *critical.threshold_certificate->problem;
    geometry2::GeometryWorkScope work(p.contact_set.assembly.limits);
    exact::IntegerLimitScope integers(p.contact_set.assembly.limits.max_integer_bits);
    check_model(p);
    const auto& seed = *input;
    const auto mu_seed = threshold_mu_seed ? *threshold_mu_seed : unit_mu_seed(p);
    if (!valid_seed(p, seed) || !valid_seed(p, mu_seed)) {
        out.call_status = "INVALID_INPUT"; out.reason = "seed_shape_mismatch"; return out;
    }
    const auto m = p.b.size(), n = p.c.size();
    const auto& basis = branch.basis;
    if (basis.size() != m || std::any_of(basis.begin(), basis.end(), [&](auto j) { return j >= n; })) {
        out.differentiability = "singular"; out.reason = "critical_basis_singular"; return out;
    }
    Matrix B(m, Vector(m));
    for (std::size_t i = 0; i < m; ++i) for (std::size_t k = 0; k < m; ++k) B[i][k] = p.A[i][basis[k]];
    const auto inv = inverse(B);
    const auto denominator = polynomial_value(branch.determinant, point);
    if (!inv || denominator == Rational(0)) {
        out.differentiability = "singular"; out.reason = "critical_basis_singular"; return out;
    }
    const auto& signs = attained ? proof.upper_signs : proof.lower_signs;
    const auto& interval = attained ? proof.upper_interval : proof.lower_interval;
    if (!signs || (interval[0] != interval[1] && signs->empty())) {
        out.reason = "critical_basis_continuation_unproved"; return out;
    }
    for (const auto& poly : branch.numerators) if (polynomial_value(poly, point) / denominator < Rational(0)) {
        out.reason = "critical_basis_infeasible_at_threshold"; return out;
    }
    const bool dual = !attained;
    if (branch.numerators.size() != (dual ? n : m) || branch.labels.size() != branch.numerators.size() ||
        (!dual && (!branch.entering || *branch.entering >= n))) throw std::logic_error("critical component dimensions");
    Vector state(m);
    if (dual) {
        for (std::size_t i = 0; i < m; ++i) for (std::size_t k = 0; k < m; ++k)
            state[i] = state[i] + (*inv)[k][i] * p.c[basis[k]];
    } else {
        for (std::size_t k = 0; k < m; ++k) for (std::size_t i = 0; i < m; ++i)
            state[k] = state[k] - (*inv)[k][i] * p.A[i][*branch.entering];
    }
    const auto mu_state = basis_variation(p.A, basis, *inv, state, mu_seed, branch.entering, dual);
    const auto parameter_state = basis_variation(p.A, basis, *inv, state, seed, branch.entering, dual);
    for (std::size_t k = 0; k < branch.numerators.size(); ++k) {
        const auto& poly = branch.numerators[k];
        if (polynomial_value(poly, point) != Rational(0)) continue;
        if (local_polynomial_sign(poly, point, dual ? 1 : -1) * denominator.sign() >= 0) continue;
        Rational partial_mu, partial_parameter;
        if (dual) {
            partial_mu = -mu_seed.dc[k]; partial_parameter = -seed.dc[k];
            for (std::size_t i = 0; i < m; ++i) {
                partial_mu = partial_mu + mu_seed.dA[i][k] * state[i] + p.A[i][k] * mu_state[i];
                partial_parameter = partial_parameter + seed.dA[i][k] * state[i] + p.A[i][k] * parameter_state[i];
            }
        } else { partial_mu = mu_state[k]; partial_parameter = parameter_state[k]; }
        const SensitivityLabel2 component_label = branch.labels[k];
        if (partial_mu == Rational(0)) {
            out.differentiability = "singular"; out.reason = "zero_implicit_denominator";
            out.implicit_components.clear();
            out.tied_labels.push_back(component_label); return out;
        }
        const auto slope = -partial_parameter / partial_mu;
        out.implicit_components.push_back({component_label, slope, partial_mu, partial_parameter, k});
    }
    if (out.implicit_components.empty()) { out.reason = "no_certified_crossing_component"; return out; }
    for (const auto& component : out.implicit_components) {
        append_unique(out.tied_labels, component.label);
        std::visit([&](const auto& item) { out.piece_jacobians.push_back({item, component.slope}); }, component.label);
    }
    out.selected_piece = SensitivitySelectedPiece2{basis, branch.kind, branch.entering};
    out.validity_conditions.push_back("临界证书基非奇异");
    out.validity_conditions.push_back("所列越零分量及方向保持有效");
    out.method = "implicit_certificate";
    const auto slope = out.implicit_components.front().slope;
    if (std::any_of(out.implicit_components.begin(), out.implicit_components.end(), [&](const auto& c) { return c.slope != slope; })) {
        out.differentiability = "tie"; out.reason = "competing_threshold_slopes"; return out;
    }
    out.differentiability = options.positive_direction_valid && options.negative_direction_valid ? "smooth" : "one_sided";
    out.display_status = "EXACT";
    if (options.positive_direction_valid) out.directional_derivative = out.right_derivative = slope;
    if (options.negative_direction_valid) out.left_derivative = slope;
    return out;
}

SensitivityResult2 evaluate_sensitivity2(const CriticalParameter2& critical, const std::optional<LimitSeed2>& input,
    const std::optional<LimitSeed2>& mu_seed, const SensitivityOptions2& options) {
    auto unavailable = [&](const std::string& reason, const std::string& status = "OK") {
        auto out = initial(critical.mathematical_status, critical.validity_conditions, options);
        out.call_status = status; out.reason = reason; out.quality = "approximate";
        out.method = "branch_certificate"; out.tied_labels.clear();
        return out;
    };
    // Threshold validation order is shared with the repaired referee. No
    // single-basis diagnostic may label a missing K jet as exact arithmetic.
    if (input && input->geometry_path && input->geometry_path->mu != Rational(0))
        return unavailable("threshold_mu_seed_not_allowed", "INVALID_INPUT");
    if (!options.positive_direction_valid && !options.negative_direction_valid)
        return unavailable("no_valid_direction");
    if (!input || !critical.exact_threshold || !critical.threshold_certificate || !critical.threshold_certificate->problem)
        return unavailable("exact_threshold_basis_and_seed_required");
    const auto& problem = *critical.threshold_certificate->problem;
    if (!valid_seed(problem, *input) || (mu_seed && !valid_seed(problem, *mu_seed)))
        return unavailable("seed_shape_mismatch", "INVALID_INPUT");
    if (!input->geometry_path) return unavailable("threshold_affine_primitives_required");
    const auto candidates = single_basis_candidate(critical, input, mu_seed, options);
    if (candidates.call_status != "OK") return unavailable(candidates.reason.value_or("threshold_branch_certificate_unavailable"), candidates.call_status);
    return branch_detail::certified_threshold(critical, *input, options, candidates);
}

std::string export_exact(const SensitivityResult2& r) {
    auto optional_text = [](const std::optional<std::string>& value) { return value ? quote(*value) : "null"; };
    auto optional_value = [](const std::optional<Rational>& value) { return value ? rational(*value) : "null"; };
    auto optional_vector = [](const std::optional<Vector>& value) { return value ? vector(*value) : "null"; };
    auto certificate = [](const std::optional<std::pair<Vector, Vector>>& value) {
        return value ? '[' + vector(value->first) + ',' + vector(value->second) + ']' : "null";
    };
    std::string selected = "null";
    if (r.selected_piece) {
        const auto& p = *r.selected_piece;
        selected = p.kind ? '[' + quote(*p.kind) + ',' + indices(p.basis) + ',' +
            (p.entering ? std::to_string(*p.entering) : "null") + ']' : indices(p.basis);
    }
    return "{\"call_status\":" + quote(r.call_status) + ",\"mathematical_status\":" + optional_text(r.mathematical_status) +
        ",\"differentiability\":" + quote(r.differentiability) + ",\"quality\":" + quote(r.quality) +
        ",\"selected_piece\":" + selected + ",\"tied_labels\":" + array(r.tied_labels, label) +
        ",\"near_labels\":" + array(r.near_labels, label) + ",\"piece_jacobians\":" + array(r.piece_jacobians, [](const auto& p) {
            return '[' + piece_label(p.label) + ',' + rational(p.derivative) + ']'; }) +
        ",\"directional_derivative\":" + optional_value(r.directional_derivative) +
        ",\"left_derivative\":" + optional_value(r.left_derivative) + ",\"right_derivative\":" + optional_value(r.right_derivative) +
        ",\"reason\":" + optional_text(r.reason) + ",\"validity_conditions\":" + array(r.validity_conditions, quote) +
        ",\"sensitivity_model\":" + quote(r.sensitivity_model) + ",\"parameter\":" + quote(r.parameter) +
        ",\"method\":" + optional_text(r.method) + ",\"primal_recession_ray\":" + optional_vector(r.primal_recession_ray) +
        ",\"dual_recession_ray\":" + optional_vector(r.dual_recession_ray) + ",\"forward_certificate\":" + certificate(r.forward_certificate) +
        ",\"reverse_certificate\":" + certificate(r.reverse_certificate) + ",\"display_status\":" + quote(r.display_status) +
        ",\"branch_certificate\":" + r.branch_certificate + ",\"implicit_components\":" + array(r.implicit_components, [](const auto& c) {
            return '[' + label(c.label) + ',' + rational(c.slope) + ',' + rational(c.partial_mu) + ',' + rational(c.partial_parameter) + ',' + std::to_string(c.index) + ']'; }) + '}';
}
} // namespace eab2::statics
