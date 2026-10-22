#include "geometry2_local.hpp"
#include "eab2/c_api.h"
#include <algorithm>
#include <sstream>

#if defined(__AVX__)
#error C1 controlled source requires the baseline x64 compilation target
#endif

namespace eab2::geometry2 {
namespace {
const Point zero{Rational(0), Rational(0)};
std::string segment_json(const Segment& segment) {
    return "[" + point_json(segment[0]) + "," + point_json(segment[1]) + "]";
}
std::string rational_json(const Rational& value) { return "\"" + value.canonical() + "\""; }
std::string bool_json(bool value) { return value ? "true" : "false"; }
void separator(std::ostringstream& out, bool& first) {
    if (!first) out << ',';
    first = false;
}
} // namespace

Rational segment_distance_squared_to_origin(const Segment& segment) {
    const Point direction = sub(segment[1], segment[0]);
    const Rational size = dot(direction, direction);
    if (size == Rational(0)) throw std::invalid_argument("distance requires a nonzero segment");
    Rational along = -dot(segment[0], direction) / size;
    along = std::max(Rational(0), std::min(Rational(1), along));
    const Point closest = add(segment[0], mul(direction, along));
    return dot(closest, closest);
}

LocalOrigin local_origin(const Entrance& entrance) {
    GeometryWorkScope work(entrance.limits());
    exact::IntegerLimitScope integer_scope(entrance.limits().max_integer_bits);
    LocalOrigin result{};
    result.body_state = entrance.membership(zero);
    result.topology_state = entrance.topology(zero);
    result.radius = Rational(1);
    std::optional<Rational> minimum;
    work.check_size(entrance.cells.size());
    for (std::size_t index = 0; index < entrance.cells.size(); ++index) {
        const Polygon& cell = entrance.cells[index];
        const auto box = numeric::exact_aabb2(cell);
        const bool box_contains = box.contains(zero); // Equal bounds are retained.
        const bool contains = box_contains && cell_state(cell, zero) >= 0;
        LocalCell local{index, index / entrance.parts_b.size(), index % entrance.parts_b.size(), cell, {}};
        std::optional<CellExclusion> excluded;
        const auto cell_sides = edges(cell);
        for (std::size_t edge_index = 0; edge_index < cell_sides.size(); ++edge_index) {
            work.step();
            const auto& edge = cell_sides[edge_index];
            const Rational sign = cross(sub(edge[1], edge[0]), sub(zero, edge[0]));
            if (!contains && !excluded && sign < Rational(0))
                excluded = CellExclusion{index, cell, box, box_contains, edge_index, edge, sign};
            if (on_segment(zero, edge[0], edge[1])) {
                if (contains) local.active_edges.push_back(edge);
            } else {
                const Rational squared = segment_distance_squared_to_origin(edge);
                if (squared <= Rational(0)) throw std::logic_error("nonincident edge has zero distance");
                result.radius_bounds.push_back({index, edge_index, edge, squared});
                work.check_size(result.radius_bounds.size());
                if (!minimum || squared < *minimum) minimum = squared;
            }
        }
        if (contains) result.cells.push_back(std::move(local));
        else {
            if (!excluded) throw std::logic_error("outside convex cell lacks a separating edge");
            result.exclusions.push_back(std::move(*excluded));
        }
    }
    // q/(1+q) is strictly positive and its square is strictly less than q.
    // No floating square root, tolerance, or supporting-line surrogate is used.
    if (minimum) result.radius = *minimum / (Rational(1) + *minimum);
    const auto& a = entrance.a;
    const auto& b = entrance.b;
    for (std::size_t i = 0; i < a.vertices.size(); ++i) {
        for (std::size_t j = 0; j < b.vertices.size(); ++j) {
            work.step();
            const auto inext = (i + 1) % a.vertices.size();
            const auto jnext = (j + 1) % b.vertices.size();
            if (on_segment(a.vertices[i], b.vertices[j], b.vertices[jnext])) {
                const Segment translated{sub(b.vertices[j], a.vertices[i]), sub(b.vertices[jnext], a.vertices[i])};
                result.raw_sources.push_back({{"VE", i, j}, translated, a.vertices[i],
                    translated[0] == zero, translated[1] == zero, a.original_vertex_ids[i],
                    {b.original_vertex_ids[j], b.original_vertex_ids[jnext]}});
            }
            if (on_segment(b.vertices[j], a.vertices[i], a.vertices[inext])) {
                const Segment translated{sub(b.vertices[j], a.vertices[i]), sub(b.vertices[j], a.vertices[inext])};
                result.raw_sources.push_back({{"EV", i, j}, translated, b.vertices[j],
                    translated[0] == zero, translated[1] == zero, b.original_vertex_ids[j],
                    {a.original_vertex_ids[i], a.original_vertex_ids[inext]}});
            }
            work.check_size(result.raw_sources.size());
        }
    }
    std::sort(result.raw_sources.begin(), result.raw_sources.end(),
              [](const OriginSource& a, const OriginSource& b) { return a.label < b.label; });
    return result;
}

int local_directional_state(const LocalOrigin& origin, const Point& direction) {
    int result = -1;
    for (const auto& cell : origin.cells) {
        bool closed = true, open = true;
        for (const auto& edge : cell.active_edges) {
            const int sign = cross(sub(edge[1], edge[0]), direction).sign();
            closed = closed && sign >= 0;
            open = open && sign > 0;
        }
        if (open) return 1;
        if (closed) result = 0;
    }
    return result;
}

std::string Entrance::local_origin_exact() const {
    const auto local = local_origin(*this);
    std::ostringstream out;
    out << "{\"schema\":\"eab2.local2.exact.v1\",\"body_state\":" << local.body_state
        << ",\"topology_state\":" << local.topology_state
        << ",\"global_subdivision_materialized\":" << bool_json(subdivision_is_materialized())
        << ",\"cell_count\":" << cells.size()
        << ",\"limits\":{\"max_work_units\":" << limits().max_work_units
        << ",\"max_elements\":" << limits().max_elements
        << ",\"max_integer_bits\":" << limits().max_integer_bits << '}'
        << ",\"radius\":" << rational_json(local.radius) << ",\"local_cells\":[";
    bool first = true;
    for (const auto& cell : local.cells) {
        separator(out, first);
        out << "{\"cell_index\":" << cell.cell_index << ",\"piece_a\":" << cell.piece_a
            << ",\"piece_b\":" << cell.piece_b << ",\"vertices\":" << polygon_json(cell.vertices)
            << ",\"active_edges\":[";
        bool first_edge = true;
        for (const auto& edge : cell.active_edges) { separator(out, first_edge); out << segment_json(edge); }
        out << "]}";
    }
    out << "],\"radius_bounds\":[";
    first = true;
    for (const auto& bound : local.radius_bounds) {
        separator(out, first);
        out << "{\"cell_index\":" << bound.cell_index << ",\"edge_index\":" << bound.edge_index
            << ",\"start\":" << point_json(bound.edge[0]) << ",\"end\":" << point_json(bound.edge[1])
            << ",\"squared_distance\":" << rational_json(bound.squared_distance) << '}';
    }
    out << "],\"cell_exclusions\":[";
    first = true;
    for (const auto& excluded : local.exclusions) {
        separator(out, first);
        out << "{\"cell_index\":" << excluded.cell_index
            << ",\"vertices\":" << polygon_json(excluded.vertices) << ",\"aabb\":["
            << rational_json(excluded.box.min_x) << ',' << rational_json(excluded.box.min_y) << ','
            << rational_json(excluded.box.max_x) << ',' << rational_json(excluded.box.max_y)
            << "],\"aabb_contains_zero\":" << bool_json(excluded.aabb_contains_zero)
            << ",\"edge_index\":" << excluded.edge_index << ",\"edge\":" << segment_json(excluded.edge)
            << ",\"signed_cross\":" << rational_json(excluded.signed_cross) << '}';
    }
    out << "],\"raw_sources\":[";
    first = true;
    for (const auto& source : local.raw_sources) {
        separator(out, first);
        out << "{\"label\":" << label_json(source.label)
            << ",\"translation_segment\":" << segment_json(source.translation_segment)
            << ",\"point\":" << point_json(source.physical_point)
            << ",\"at_start\":" << bool_json(source.at_start) << ",\"at_end\":" << bool_json(source.at_end)
            << ",\"vertex_id\":" << source.vertex_id << ",\"edge_vertex_ids\":["
            << source.edge_vertex_ids[0] << ',' << source.edge_vertex_ids[1] << "]}";
    }
    out << "],\"source\":\"original_rings_and_exact_convex_cells\","
        << "\"observable\":\"local_translation_geometry_not_mechanical_constraints\"}";
    return out.str();
}
} // namespace eab2::geometry2
