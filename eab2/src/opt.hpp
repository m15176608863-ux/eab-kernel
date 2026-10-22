#pragma once
#include "exact.hpp"
#include <cstddef>
#include <optional>
#include <string>
#include <vector>

// Private cross-cutting optimization API. No geometry/contact dependency.
namespace eab2::opt {
using Rational = exact::Rational;
using Vector = std::vector<Rational>;
using Matrix = std::vector<Vector>;

enum class Status { optimal, infeasible, unbounded };
const char* status_name(Status status);

// Basis indices n+i denote the artificial unit column after exact b-sign flips.
// A candidate is only a hint: every claimed status is reconstructed exactly.
struct Candidate {
    Status status = Status::optimal;
    std::vector<std::size_t> basis;
    std::optional<std::size_t> entering;
};
struct Options {
    std::size_t max_pivots = 1000000;
    std::optional<Candidate> candidate;
};
struct Statistics {
    std::size_t pivots = 0; // Includes artificial-column cleanup and auxiliaries.
    std::size_t auxiliary_solves = 0;
    // Stored input, basis inverse and certificate components, not all temporary
    // integer products inside Rational arithmetic.
    std::size_t max_stored_integer_bits = 0;
    bool candidate_accepted = false;
    bool candidate_warm_started = false;
    bool bland_used = false;
};
struct Result {
    Status status = Status::optimal;
    // OPTIMAL: primal x and dual y, plus finite objective.
    // INFEASIBLE: y is Farkas (A^T y <= 0, b^T y > 0), no x/objective.
    // UNBOUNDED: feasible x0 and normalized improving ray, no y/objective.
    Vector exact_x, exact_y, exact_ray;
    std::optional<Rational> exact_objective;
    // Status-detecting basis. For UNBOUNDED, x0/ray are auxiliary LP witnesses
    // and are not asserted to be basic in this original detection basis.
    std::vector<std::size_t> basis;
    Statistics stats;
};

// Standard form min c^T x, A x=b, x>=0. Inputs are the original exact model.
// This first implementation uses exact cold-start by default; optional floating
// candidates may be supplied, but floating filtering never decides an answer.
Result solve(const Matrix& A, const Vector& b, const Vector& c,
             const Options& options = {});
Result maximize(const Matrix& A, const Vector& b, const Vector& c,
                const Options& options = {});

// Independently reconstruct a candidate basis. A false claim returns nullopt.
// UNBOUNDED here already includes x0 and a ray with c^T ray=-1; solve obtains
// the public witnesses from auxiliary feasibility LPs as required by design.
std::optional<Result> certify_candidate(const Matrix& A, const Vector& b,
                                        const Vector& c, const Candidate& candidate);

// Direct original-model checker, independent of basis/simplex state. For max,
// optimal dual is A^T y>=c and the improving normalization is c^T ray=1.
bool verify_certificate(const Matrix& A, const Vector& b, const Vector& c,
                        const Result& result, bool maximize_objective = false);
std::string export_exact(const Result& result, bool maximize_objective = false);

// A x=0, x>=0, normalizer^T x=1; objective is zero. This rules out the trivial
// homogeneous solution and is reusable by contact and later statics callers.
Result homogeneous_feasibility(const Matrix& A, const Vector& normalizer,
                               const Options& options = {});
} // namespace eab2::opt
