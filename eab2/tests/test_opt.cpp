#include "opt.hpp"
#include <array>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

using namespace eab2::opt;
namespace {
std::size_t checks = 0;
void require(bool condition, const char* name) {
    ++checks;
    if (!condition) throw std::runtime_error(name);
}
template <class Exception, class Function> void fails(Function action, const char* name) {
    ++checks;
    try { action(); }
    catch (const Exception&) { return; }
    throw std::runtime_error(name);
}
Rational q(std::int64_t numerator, std::int64_t denominator) {
    return Rational(eab2::exact::Int(numerator), eab2::exact::Int(denominator));
}
Rational power(int exponent) {
    using eab2::exact::Int;
    return exponent >= 0 ? Rational(Int(1) << static_cast<std::size_t>(exponent))
                         : Rational(Int(1), Int(1) << static_cast<std::size_t>(-exponent));
}
Rational inner(const Vector& a, const Vector& b) {
    Rational value;
    for (std::size_t i = 0; i < a.size(); ++i) value = value + a[i] * b[i];
    return value;
}
// Independent oracle: elementary original-matrix equations/inequalities only;
// does not call production verify_certificate, basis reconstruction or simplex.
void independent_certificate(const Matrix& A, const Vector& b, const Vector& c,
                             const Result& result, bool maximize = false) {
    const auto m = b.size(), n = c.size();
    if (result.status == Status::infeasible) {
        require(result.exact_y.size() == m && inner(b, result.exact_y) > Rational(0), "Farkas positive separation");
        for (std::size_t j = 0; j < n; ++j) {
            Rational value;
            for (std::size_t i = 0; i < m; ++i) value = value + A[i][j] * result.exact_y[i];
            require(value <= Rational(0), "Farkas every original column");
        }
        return;
    }
    require(result.exact_x.size() == n, "primal dimension");
    for (const auto& x : result.exact_x) require(x >= Rational(0), "nonnegative primal");
    for (std::size_t i = 0; i < m; ++i) require(inner(A[i], result.exact_x) == b[i], "original primal row equality");
    if (result.status == Status::unbounded) {
        require(result.exact_ray.size() == n, "unbounded ray dimension");
        for (const auto& value : result.exact_ray) require(value >= Rational(0), "nonnegative ray");
        for (const auto& row : A) require(inner(row, result.exact_ray) == Rational(0), "ray original nullspace");
        require(inner(c, result.exact_ray) == Rational(maximize ? 1 : -1), "normalized strict improvement");
        return;
    }
    require(result.status == Status::optimal && result.exact_objective && result.exact_y.size() == m,
            "finite optimal fields");
    for (std::size_t j = 0; j < n; ++j) {
        Rational value;
        for (std::size_t i = 0; i < m; ++i) value = value + A[i][j] * result.exact_y[i];
        require(maximize ? value >= c[j] : value <= c[j], "original dual column inequality");
    }
    require(inner(c, result.exact_x) == *result.exact_objective, "primal objective identity");
    require(inner(b, result.exact_y) == *result.exact_objective, "exact zero duality gap");
}

void candidate_reconstruction_rejects_lies() {
    const Matrix A{{1, 1, 1, 0}, {1, 3, 0, 1}};
    const Vector b{4, 6}, c{-3, -2, 0, 0};
    const auto good = certify_candidate(A, b, c, {Status::optimal, {0, 3}, {}});
    require(good && good->exact_objective == Rational(-12), "known optimal candidate");
    for (const Candidate bad : std::vector<Candidate>{
            {Status::optimal, {2, 3}, {}}, {Status::optimal, {1, 3}, {}},
            {Status::infeasible, {0, 3}, {}}, {Status::unbounded, {0, 3}, 1},
            {Status::optimal, {0, 0}, {}}, {Status::optimal, {99, 3}, {}},
            {Status::optimal, {0}, {}}, {Status::optimal, {0, 2}, {}}})
        require(!certify_candidate(A, b, c, bad), "wrong candidate rejected");
    const Matrix Ai{{1, 1}, {1, 1}};
    require(bool(certify_candidate(Ai, {1, 2}, {1, 0}, {Status::infeasible, {0, 3}, {}})), "valid Farkas candidate");
    require(!certify_candidate(Ai, {1, 2}, {1, 0}, {Status::infeasible, {2, 3}, {}}), "invalid Farkas column rejected");
    require(!certify_candidate(Ai, {1, 2}, {1, 0}, {Status::optimal, {0, 3}, {}}), "nonzero artificial rejected");
    require(!certify_candidate({{-1, 1}, {0, 1}}, {0, 0}, {-1, 0}, {Status::unbounded, {2, 3}, 0}),
            "artificial ray movement rejected");
    require(!certify_candidate({{1, -1}}, {1}, {0, 1}, {Status::unbounded, {0}, 1}),
            "recession without improvement rejected");
    Options valid;
    valid.candidate = Candidate{Status::optimal, {0, 3}, {}};
    const auto accepted = solve(A, b, c, valid);
    require(accepted.stats.candidate_accepted && accepted.stats.pivots == 0, "accepted exact reconstruction no pivots");
    const std::array<Matrix, 3> systems{A, Ai, Matrix{{1, -1, 0}, {0, 1, -1}}};
    const std::array<Vector, 3> rhs{b, Vector{1, 2}, Vector{1, 0}};
    const std::array<Vector, 3> costs{c, Vector{1, 0}, Vector{-1, 0, 0}};
    const std::array<Status, 3> states{Status::optimal, Status::infeasible, Status::unbounded};
    for (std::size_t k = 0; k < systems.size(); ++k) {
        for (const Candidate lie : std::vector<Candidate>{
                {Status::optimal, {99, 99}, {}}, {Status::infeasible, {0, 1}, {}},
                {Status::unbounded, {0, 1}, 0}, {Status::optimal, {0, 1}, {}},
                {Status::optimal, {}, {}}}) {
            Options options;
            options.candidate = lie;
            const auto result = solve(systems[k], rhs[k], costs[k], options);
            require(result.status == states[k], "lying hint cannot change mathematical status");
            independent_certificate(systems[k], rhs[k], costs[k], result);
            if (k == 0) require(result.exact_objective == Rational(-12), "lying hint cannot change optimum");
        }
    }
}

void three_statuses_and_signs() {
    const Matrix A{{-1, -1}, {1, 0}};
    const Vector b{-4, 1}, c{3, 7};
    const auto minimum = solve(A, b, c);
    const auto maximum = maximize(A, b, c);
    independent_certificate(A, b, c, minimum);
    independent_certificate(A, b, c, maximum, true);
    require(minimum.exact_objective == Rational(24) && maximum.exact_objective == Rational(24), "negative RHS row flips");
    require(minimum.exact_y == maximum.exact_y, "max original dual sign semantics");
    const auto maximum2 = maximize({{1, 1, 1, 0}, {1, 3, 0, 1}}, {4, 6}, {3, 2, 0, 0});
    require(maximum2.exact_objective == Rational(12) && maximum2.exact_y == Vector({3, 0}), "maximum dual not left negated");
    for (const Vector rhs : {Vector{1, 2}, Vector{-1, -2}}) {
        const Matrix same{{1, 1}, {1, 1}};
        independent_certificate(same, rhs, {1, 0}, maximize(same, rhs, {1, 0}), true);
    }
    const Matrix chain{{1, -1, 0}, {0, 1, -1}};
    const auto unbounded = solve(chain, {7, 3}, {-2, 0, 0});
    independent_certificate(chain, {7, 3}, {-2, 0, 0}, unbounded);
    require(unbounded.stats.auxiliary_solves == 2, "unbounded two auxiliary LPs");
    require(unbounded.exact_x != Vector(3), "unbounded actual feasible point not placeholder zeros");
    const auto max_unbounded = maximize(chain, {7, 3}, {2, 0, 0});
    independent_certificate(chain, {7, 3}, {2, 0, 0}, max_unbounded, true);
    const auto json = export_exact(max_unbounded, true);
    require(json.find("\"status\":\"unbounded\"") != std::string::npos &&
            json.find("\"sense\":\"max\"") != std::string::npos &&
            json.find("\"objective\":null") != std::string::npos, "exact export explicit status and objective");
}

void empty_and_redundant_models() {
    independent_certificate({}, {}, {}, solve({}, {}, {}));
    independent_certificate({}, {}, {0, 1, 2}, solve({}, {}, {0, 1, 2}));
    const auto no_rows = solve({}, {}, {0, -3, -7});
    independent_certificate({}, {}, {0, -3, -7}, no_rows);
    require(no_rows.status == Status::unbounded, "zero-row exact objective used");
    independent_certificate({{}, {}}, {0, 0}, {}, solve({{}, {}}, {0, 0}, {}));
    independent_certificate({{}, {}}, {0, -2}, {}, solve({{}, {}}, {0, -2}, {}));
    const Matrix A{{1, -1, 0}, {2, -2, 0}, {0, 0, 0}};
    const auto redundant = solve(A, {0, 0, 0}, {1, -1, 3});
    independent_certificate(A, {0, 0, 0}, {1, -1, 3}, redundant);
    require(redundant.exact_objective == Rational(0), "redundant artificial rows retained at zero");
    const auto bounded = solve({{-1, 1}, {0, 1}}, {0, 0}, {-1, 0});
    require(bounded.status == Status::optimal && bounded.exact_objective == Rational(0), "artificial blocker preserves boundedness");
}

void exact_scale_and_resolution() {
    const auto tiny = power(-1400), huge = power(1400);
    const auto signed_rhs = solve({{1, -1}}, {-tiny}, {1, 0});
    independent_certificate({{1, -1}}, {-tiny}, {1, 0}, signed_rhs);
    require(signed_rhs.exact_x == Vector({0, tiny}), "RHS below binary64 exact sign");
    require(solve({}, {}, {-tiny}).status == Status::unbounded, "objective below binary64 exact sign");
    const auto overflow = solve({{tiny, 1, -1}}, {huge}, {0, 1, 1});
    independent_certificate({{tiny, 1, -1}}, {huge}, {0, 1, 1}, overflow);
    require(overflow.exact_x[0] == huge / tiny && overflow.stats.max_stored_integer_bits >= 2801,
            "exact primal exceeds display range with measured bit length");
    for (const int sign : {-1, 1}) {
        const auto result = solve({{huge, huge}}, {huge}, {Rational(sign) * tiny, Rational(sign) * tiny / Rational(2)});
        require(result.exact_x == (sign > 0 ? Vector{0, 1} : Vector{1, 0}), "sub-display dual selects correct column");
    }
    for (const int exponent : {20, 80, 500}) {
        const auto epsilon = power(-exponent);
        const Matrix A{{1, -1, 0}, {-1, Rational(1) + epsilon, -1}};
        const auto result = solve(A, {1, 0}, {0, 1, 0});
        independent_certificate(A, {1, 0}, {0, 1, 0}, result);
        require(result.exact_objective == Rational(1) / epsilon, "near-parallel feasible exact optimum");
    }
}

// Independent optimum oracle: enumerate all six 2-column intersections using
// closed-form determinants. It does not share any production LP algorithm.
Rational exhaustive_two_rows(const Matrix& A, const Vector& b, const Vector& c) {
    std::optional<Rational> optimum;
    for (std::size_t j = 0; j < c.size(); ++j) {
        for (std::size_t k = j + 1; k < c.size(); ++k) {
            const auto determinant = A[0][j] * A[1][k] - A[0][k] * A[1][j];
            if (!determinant.sign()) continue;
            const auto x = (b[0] * A[1][k] - b[1] * A[0][k]) / determinant;
            const auto y = (A[0][j] * b[1] - A[1][j] * b[0]) / determinant;
            if (x.sign() < 0 || y.sign() < 0) continue;
            const auto value = c[j] * x + c[k] * y;
            if (!optimum || value < *optimum) optimum = value;
        }
    }
    if (!optimum) throw std::runtime_error("bounded exhaustive test lacks vertex");
    return *optimum;
}
void asymmetric_scale_grid() {
    std::mt19937 rng(9137);
    for (int sample = 0; sample < 60; ++sample) {
        const auto next = [&]() { return static_cast<std::int64_t>(rng() % 19 + 1); };
        const Matrix original{{Rational(next()), Rational(next()), 1, 0},
                              {Rational(next()), Rational(next()), 0, 1}};
        const Vector rhs{Rational(sample % 3 ? next() : 0), Rational(next())};
        const Vector cost{-Rational(next()), -Rational(next()), 0, 0};
        const auto truth = exhaustive_two_rows(original, rhs, cost);
        for (int variant = 0; variant < 6; ++variant) {
            Matrix A = original;
            Vector b = rhs, c = cost;
            Rational expected = truth;
            if (variant == 1) {
                for (auto& value : A[1]) value = value * power(-80);
                b[1] = b[1] * power(-80);
            } else if (variant == 2) {
                for (auto& row : A) row[0] = row[0] * power(200);
                c[0] = c[0] * power(200);
            } else if (variant == 3) {
                for (auto& value : b) value = value * power(400);
                expected = expected * power(400);
            } else if (variant == 4) {
                for (auto& value : c) value = value * power(-500);
                expected = expected * power(-500);
            } else if (variant == 5) {
                A.push_back(A[0]);
                b.push_back(b[0]);
            }
            const auto result = solve(A, b, c);
            independent_certificate(A, b, c, result);
            require(result.exact_objective == expected, "asymmetric scale grid independent exact optimum");
        }
    }
}

void cycling_terminates_and_budget_fails_loud() {
    const std::array<Matrix, 3> matrices{
        Matrix{{1, 0, 0, q(1, 4), -8, -1, 9}, {0, 1, 0, q(1, 2), -12, q(-1, 2), 3}, {0, 0, 1, 0, 0, 1, 0}},
        Matrix{{-2, -9, 1, 9, 1, 0, 0}, {q(1, 3), 1, q(-1, 3), -2, 0, 1, 0}, {2, 3, -1, -12, 0, 0, 1}},
        Matrix{{q(1, 2), q(-11, 2), q(-5, 2), 9, 1, 0, 0}, {q(1, 2), q(-3, 2), q(-1, 2), 1, 0, 1, 0}, {1, 0, 0, 0, 0, 0, 1}}};
    const std::array<Vector, 3> rhs{Vector{0, 0, 1}, Vector{0, 0, 2}, Vector{0, 0, 1}};
    const std::array<Vector, 3> costs{Vector{0, 0, 0, q(-3, 4), 20, q(-1, 2), 6}, Vector{-2, -3, 1, 12, 0, 0, 0}, Vector{-10, 57, 9, 24, 0, 0, 0}};
    const std::array<std::vector<std::size_t>, 3> starts{std::vector<std::size_t>{0, 1, 2}, {4, 5, 6}, {4, 5, 6}};
    bool observed_bland = false;
    for (std::size_t i = 0; i < matrices.size(); ++i) {
        Options options;
        options.max_pivots = 1000;
        options.candidate = Candidate{Status::optimal, starts[i], {}};
        const auto result = solve(matrices[i], rhs[i], costs[i], options);
        independent_certificate(matrices[i], rhs[i], costs[i], result);
        require(result.status == Status::optimal && result.stats.candidate_warm_started, "cycling example exact warm start terminates");
        observed_bland = observed_bland || result.stats.bland_used;
    }
    require(observed_bland, "cycling examples exercise Bland anti-cycling path");
    Options no_work;
    no_work.max_pivots = 0;
    fails<eab2::exact::ResourceLimit>([&] { solve({{1}}, {1}, {1}, no_work); }, "pivot budget must fail loud");
    require(solve({}, {}, {1}, no_work).status == Status::optimal, "zero-pivot problem permitted at zero work");
    const auto large = power(100);
    fails<eab2::exact::ResourceLimit>([&] {
        const eab2::exact::IntegerLimitScope limit(32);
        solve({{large}}, {1}, {1});
    }, "integer work limit must fail loud");
}

void normalization_and_invalid_inputs() {
    const auto positive = homogeneous_feasibility({{1, -1}}, {1, 1});
    require(positive.status == Status::optimal && positive.exact_x == Vector({q(1, 2), q(1, 2)}), "homogeneous normalization excludes zero");
    const auto impossible = homogeneous_feasibility({{1, 1}}, {1, 1});
    require(impossible.status == Status::infeasible, "zero-only homogeneous cone infeasible after normalization");
    independent_certificate({{1, 1}, {1, 1}}, {0, 1}, {0, 0}, impossible);
    fails<std::invalid_argument>([] { solve({{1}}, {}, {1}); }, "RHS shape mismatch rejected");
    fails<std::invalid_argument>([] { solve({{1, 2}}, {1}, {1}); }, "ragged model rejected");
    fails<std::invalid_argument>([] { homogeneous_feasibility({{1, 2}}, {1}); }, "normalizer shape mismatch rejected");
    auto result = solve({{1, 1}}, {1}, {1, 2});
    result.exact_x[0] = Rational(2);
    require(!verify_certificate({{1, 1}}, {1}, {1, 2}, result), "checker rejects corrupted primal");
    result = solve({{1, 1}}, {1}, {1, 2});
    result.exact_y[0] = Rational(3);
    require(!verify_certificate({{1, 1}}, {1}, {1, 2}, result), "checker rejects corrupted dual");
    result = solve({{1, -1}}, {1}, {-1, 0});
    result.exact_ray[0] = Rational(0);
    require(!verify_certificate({{1, -1}}, {1}, {-1, 0}, result), "checker rejects corrupted improving ray");
}
} // namespace

int main() {
    try {
        candidate_reconstruction_rejects_lies();
        three_statuses_and_signs();
        empty_and_redundant_models();
        exact_scale_and_resolution();
        asymmetric_scale_grid();
        cycling_terminates_and_budget_fails_loud();
        normalization_and_invalid_inputs();
        std::cout << "EAB2_OPT_TESTS checks=" << checks << " failed=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "EAB2_OPT_TESTS checks=" << checks << " failed=1 detail=" << error.what() << '\n';
        return 1;
    }
}
