#pragma once
#include "l1.hpp"
#include <array>
#include <optional>
#include <string>
#include <utility>
#include <vector>

// Exact profile1 statics. Associated flow is an unsafe-side upper-bound model
// relative to non-associated friction; unboundedness does not imply locking.
namespace eab2::statics {
using Rational = exact::Rational;
using Vector = opt::Vector;
using Matrix = opt::Matrix;
using Point = geometry2::Point;
using Wrench = std::array<Rational, 3>;
struct BodyLoads2 {
    Wrench dead{0, 0, 0};
    Wrench live{0, 0, 0};
};
using Loads2 = std::vector<BodyLoads2>;
struct ColumnLabel2 {
    std::optional<contact::ContactLabel2> contact;
    int sign = 1;
};
struct LimitProblem2 {
    Matrix A;
    Vector b, c;
    std::vector<std::pair<std::string, std::size_t>> row_labels;
    std::vector<ColumnLabel2> column_labels;
    std::vector<Point> reference_points, dof_anchors;
    Rational mu;
    contact::ContactSet2 contact_set;
    Loads2 loads;
    std::string profile = "profile1";
    std::string sensitivity_model = "ideal_exact_2d";
};
struct LimitResult2 {
    std::string call_status = "OK";
    std::optional<std::string> mathematical_status;
    std::string display_status = "NOT_APPLICABLE";
    std::optional<Rational> exact_value;
    std::optional<Vector> exact_x, exact_y, feasible_point, improving_ray, farkas;
    // OPTIMAL dual coordinates are anchor twists: G^T y >= 0, live^T y >= 1.
    std::optional<Vector> mechanism;
    std::optional<LimitProblem2> problem;
    std::optional<std::string> reason;
    std::vector<std::size_t> basis;
    std::string sensitivity_model = "ideal_exact_2d";
    std::vector<std::string> validity_conditions;
    opt::Statistics stats;
};

LimitProblem2 build_limit_problem2(const contact::ContactSet2& contacts,
                                  const Loads2& loads, const Rational& mu);
LimitResult2 solve_limit_problem2(const LimitProblem2& problem,
                                 const opt::Options& options = {});
LimitResult2 limit_load_ideal_exact_2d(const contact::ContactSet2& contacts,
                                    const Loads2& loads, const Rational& mu,
                                    const opt::Options& options = {});
LimitResult2 limit_load_ideal_exact_2d(const contact::Assembly2& assembly,
                                    const Loads2& loads, const Rational& mu,
                                    const opt::Options& options = {});
std::string export_exact(const ColumnLabel2& label);
std::string export_exact(const LimitProblem2& problem);
std::string export_exact(const LimitResult2& result);
} // namespace eab2::statics
