#pragma once
#include "sensitivity.hpp"

// Original-vertex jets. No scene parameter names or finite differences here.
namespace eab2::statics {
struct VertexSeed2 {
    std::string body_id;
    std::size_t vertex_id;
    Point derivative;
};
struct BodySeed2 {
    std::string body_id;
    Wrench dead{0, 0, 0}, live{0, 0, 0};
    Point dof_anchor{0, 0};
};
struct GeometrySeed2 {
    std::string parameter = "mu";
    std::vector<VertexSeed2> vertices;
    std::vector<BodySeed2> bodies;
    Rational mu;
};

// Both ID tables must be complete and sorted by body_id/original vertex ID.
// A shared geometric vertex has one velocity, even across different bodies.
void validate_geometry_seed2(const contact::ContactSet2&, const GeometrySeed2&);
LimitSeed2 propagate_geometry_seed2(const LimitProblem2&, const GeometrySeed2&);
} // namespace eab2::statics
