#include "geometry_seed.hpp"
#include <algorithm>
#include <map>
#include <stdexcept>

namespace eab2::statics {
namespace {
using VertexId = std::pair<std::string, std::size_t>;
struct IndexedSeed {
    std::map<VertexId, Point> points, velocities;
    std::map<Point, Point> point_velocities;
    std::map<std::string, const BodySeed2*> bodies;
};
IndexedSeed index_seed(const contact::ContactSet2& contacts, const GeometrySeed2& seed) {
    geometry2::GeometryWorkScope work(contacts.assembly.limits);
    IndexedSeed index;
    std::vector<std::string> ids;
    for (const auto& body : contacts.assembly.bodies) {
        ids.push_back(body.body_id);
        const auto& g = body.geometry;
        if (g.vertices.size() != g.original_vertex_ids.size())
            throw std::logic_error("original vertex identity missing");
        for (std::size_t k = 0; k < g.vertices.size(); ++k) {
            work.step();
            if (!index.points.emplace(VertexId{body.body_id, g.original_vertex_ids[k]}, g.vertices[k]).second)
                throw std::logic_error("duplicate original vertex identity");
        }
    }
    std::sort(ids.begin(), ids.end());
    if (std::adjacent_find(ids.begin(), ids.end()) != ids.end())
        throw std::logic_error("duplicate body identity");
    if (seed.bodies.size() != ids.size() || seed.vertices.size() != index.points.size())
        throw std::invalid_argument("geometry seed identity count mismatch");
    for (std::size_t k = 0; k < ids.size(); ++k) {
        if (seed.bodies[k].body_id != ids[k])
            throw std::invalid_argument("geometry seed body identity order mismatch");
        index.bodies.emplace(ids[k], &seed.bodies[k]);
    }
    auto expected = index.points.begin();
    for (const auto& vertex : seed.vertices) {
        work.step();
        const VertexId key{vertex.body_id, vertex.vertex_id};
        if (expected == index.points.end() || key != expected->first)
            throw std::invalid_argument("geometry seed original vertex identity order mismatch");
        index.velocities.emplace(key, vertex.derivative);
        const auto [at, inserted] = index.point_velocities.emplace(expected->second, vertex.derivative);
        if (!inserted && at->second != vertex.derivative)
            throw std::invalid_argument("geometry jet breaks a shared vertex");
        ++expected;
    }
    return index;
}
Vector project_derivative(const contact::Body2& body, const Wrench& value,
                          const Wrench& derivative, const Point& anchor_seed) {
    if (body.boundary_type == "FIXED_BODY") return {};
    const Point offset = geometry2::sub(body.dof_anchor, body.reference_point);
    const Wrench full{derivative[0], derivative[1], derivative[2]
        - geometry2::cross(offset, Point{derivative[0], derivative[1]})
        - geometry2::cross(anchor_seed, Point{value[0], value[1]})};
    Vector out;
    for (std::size_t k = 0; k < 3; ++k) if (body.dof_mask[k]) out.push_back(full[k]);
    return out;
}
} // namespace

void validate_geometry_seed2(const contact::ContactSet2& contacts, const GeometrySeed2& seed) {
    exact::IntegerLimitScope integers(contacts.assembly.limits.max_integer_bits);
    (void)index_seed(contacts, seed);
}

LimitSeed2 propagate_geometry_seed2(const LimitProblem2& problem, const GeometrySeed2& seed) {
    const auto& contacts = problem.contact_set;
    const auto& assembly = contacts.assembly;
    geometry2::GeometryWorkScope work(assembly.limits);
    exact::IntegerLimitScope integers(assembly.limits.max_integer_bits);
    const auto index = index_seed(contacts, seed);
    const std::size_t rows = problem.b.size(), columns = problem.c.size();
    if (problem.loads.size() != assembly.bodies.size() ||
        contacts.constraints.size() > (columns ? (columns - 1) / 2 : 0) ||
        columns != 2 * contacts.constraints.size() + 1 || problem.A.size() != rows)
        throw std::logic_error("geometry jet requires an original contact problem");
    if (rows && columns > work.limits.max_elements / rows)
        throw exact::ResourceLimit("geometry seed matrix element limit exceeded");
    LimitSeed2 out{Matrix(rows, Vector(columns)), Vector(rows), Vector(columns), seed.parameter};
    out.geometry_path = std::make_shared<GeometrySeed2>(seed);
    std::size_t j = 0;
    for (const auto& contact : contacts.constraints) {
        const auto& label = contact.label;
        const VertexId start{label.edge_body, label.edge[0]}, end{label.edge_body, label.edge[1]};
        if (!index.points.contains(start) || !index.points.contains(end) ||
            !index.point_velocities.contains(contact.point))
            throw std::invalid_argument("contact seed original feature unavailable");
        const Point edge = geometry2::sub(index.points.at(end), index.points.at(start));
        const Rational sense = edge == contact.tangent ? Rational(1) : Rational(-1);
        if (geometry2::mul(edge, sense) != contact.tangent)
            throw std::logic_error("contact tangent is not its original edge");
        const Point dt = geometry2::mul(geometry2::sub(index.velocities.at(end), index.velocities.at(start)), sense);
        const Point dp = index.point_velocities.at(contact.point);
        const auto& t = contact.tangent;
        for (const int sign : {-1, 1}) {
            const Rational s(sign);
            const Point force{-t[1] + s * problem.mu * t[0], t[0] + s * problem.mu * t[1]};
            const Point df{-dt[1] + s * (seed.mu * t[0] + problem.mu * dt[0]),
                           dt[0] + s * (seed.mu * t[1] + problem.mu * dt[1])};
            std::size_t i = 0;
            for (std::size_t k = 0; k < assembly.bodies.size(); ++k) {
                const auto& body = assembly.bodies[k];
                if (body.boundary_type == "FIXED_BODY") continue;
                const Rational side(static_cast<int>(k == contact.a) - static_cast<int>(k == contact.b));
                const auto& jet = *index.bodies.at(body.body_id);
                // y/mechanism are anchor twists, not reference-point twists.
                const Point arm = geometry2::sub(contact.point, body.dof_anchor);
                const Point velocity = geometry2::sub(dp, jet.dof_anchor);
                const Wrench derivative{side * df[0], side * df[1],
                    side * (geometry2::cross(velocity, force) + geometry2::cross(arm, df))};
                for (std::size_t axis = 0; axis < 3; ++axis) if (body.dof_mask[axis]) {
                    work.step();
                    if (i >= rows) throw std::logic_error("geometry seed row count mismatch");
                    out.dA[i++][j] = derivative[axis];
                }
            }
            if (i != rows) throw std::logic_error("geometry seed row count mismatch");
            ++j;
        }
    }
    std::size_t i = 0;
    for (std::size_t k = 0; k < assembly.bodies.size(); ++k) {
        const auto& body = assembly.bodies[k];
        const auto& jet = *index.bodies.at(body.body_id);
        const auto dead = project_derivative(body, problem.loads[k].dead, jet.dead, jet.dof_anchor);
        const auto live = project_derivative(body, problem.loads[k].live, jet.live, jet.dof_anchor);
        for (std::size_t axis = 0; axis < dead.size(); ++axis) {
            work.step();
            if (i >= rows) throw std::logic_error("geometry seed load row count mismatch");
            out.dA[i][j] = live[axis]; // The live coefficient belongs in A.
            out.db[i++] = -dead[axis];
        }
    }
    if (i != rows) throw std::logic_error("geometry seed load row count mismatch");
    return out;
}
} // namespace eab2::statics
