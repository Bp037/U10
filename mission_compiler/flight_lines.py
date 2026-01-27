"""Generate flight lines from input geometry."""

from __future__ import annotations

import math
from typing import List, Tuple

from .geo import (
    XY,
    coords_to_xy,
    distance,
    extend_line,
    reference_from_coords,
    rotate,
    rotate_points,
    xy_to_coords,
)
from .models import InputGeometry, LatLon, Line, MissionPlan, Waypoint


def plan_flight_lines(
    geometry: InputGeometry,
    extension_m: float,
    line_spacing_m: float,
    nominal_alt_m: float,
) -> MissionPlan:
    if geometry.geometry_type == "LineString":
        return _plan_line_string(geometry, extension_m, nominal_alt_m)
    if geometry.geometry_type == "Polygon":
        return _plan_polygon(geometry, extension_m, line_spacing_m, nominal_alt_m)
    raise ValueError(f"Unsupported geometry type: {geometry.geometry_type}")


def _plan_line_string(
    geometry: InputGeometry,
    extension_m: float,
    nominal_alt_m: float,
) -> MissionPlan:
    coords = geometry.coordinates
    if len(coords) < 2:
        raise ValueError("LineString requires at least two coordinates.")

    ref_lat, ref_lon = reference_from_coords(coords)
    xy_points = coords_to_xy(coords, ref_lat, ref_lon)

    start_dir = _unit_direction(xy_points[0], xy_points[1])
    end_dir = _unit_direction(xy_points[-2], xy_points[-1])
    extended_start = XY(
        x=xy_points[0].x - start_dir[0] * extension_m,
        y=xy_points[0].y - start_dir[1] * extension_m,
    )
    extended_end = XY(
        x=xy_points[-1].x + end_dir[0] * extension_m,
        y=xy_points[-1].y + end_dir[1] * extension_m,
    )

    extended_path_xy = [extended_start] + xy_points[1:-1] + [extended_end]
    waypoints = [
        Waypoint(lat=point.lat, lon=point.lon, alt_m=nominal_alt_m)
        for point in xy_to_coords(extended_path_xy, ref_lat, ref_lon)
    ]

    flight_lines = []
    if len(waypoints) >= 2:
        for idx in range(len(waypoints) - 1):
            start = LatLon(lat=waypoints[idx].lat, lon=waypoints[idx].lon)
            end = LatLon(lat=waypoints[idx + 1].lat, lon=waypoints[idx + 1].lon)
            flight_lines.append(Line(start=start, end=end))

    return MissionPlan(
        geometry_type=geometry.geometry_type,
        waypoints=waypoints,
        flight_lines=flight_lines,
        warnings=[
            "Turns between polyline vertices are non-data zones.",
        ],
    )


def _plan_polygon(
    geometry: InputGeometry,
    extension_m: float,
    line_spacing_m: float,
    nominal_alt_m: float,
) -> MissionPlan:
    coords = geometry.coordinates
    if len(coords) < 3:
        raise ValueError("Polygon requires at least three coordinates.")

    ref_lat, ref_lon = reference_from_coords(coords)
    xy_points = coords_to_xy(coords, ref_lat, ref_lon)
    if xy_points[0] != xy_points[-1]:
        xy_points = xy_points + [xy_points[0]]

    angle = _principal_axis_angle(xy_points)
    rotated = rotate_points(xy_points, -angle)

    min_y = min(p.y for p in rotated)
    max_y = max(p.y for p in rotated)

    scanlines = _scanline_positions(min_y, max_y, line_spacing_m)
    segments: List[Tuple[XY, XY]] = []
    for y in scanlines:
        intersections = _scanline_intersections(rotated, y)
        for start_x, end_x in intersections:
            segments.append((XY(start_x, y), XY(end_x, y)))

    flight_lines: List[Line] = []
    waypoints: List[Waypoint] = []
    for idx, (start, end) in enumerate(segments):
        if idx % 2 == 1:
            start, end = end, start
        extended_start, extended_end = extend_line(start, end, extension_m)
        unrotated_start = rotate(extended_start, angle)
        unrotated_end = rotate(extended_end, angle)
        start_ll = xy_to_coords([unrotated_start], ref_lat, ref_lon)[0]
        end_ll = xy_to_coords([unrotated_end], ref_lat, ref_lon)[0]
        flight_lines.append(Line(start=start_ll, end=end_ll))
        waypoints.append(Waypoint(lat=start_ll.lat, lon=start_ll.lon, alt_m=nominal_alt_m))
        waypoints.append(Waypoint(lat=end_ll.lat, lon=end_ll.lon, alt_m=nominal_alt_m))

    if not flight_lines:
        raise ValueError("Polygon produced no flight lines. Check geometry size.")

    return MissionPlan(
        geometry_type=geometry.geometry_type,
        waypoints=waypoints,
        flight_lines=flight_lines,
        warnings=[
            "Turns between scan lines are non-data zones.",
        ],
    )


def _unit_direction(start: XY, end: XY) -> Tuple[float, float]:
    length = distance(start, end)
    if length == 0:
        raise ValueError("Cannot compute direction for zero-length segment.")
    return (end.x - start.x) / length, (end.y - start.y) / length


def _principal_axis_angle(points: List[XY]) -> float:
    if not points:
        return 0.0
    mean_x = sum(p.x for p in points) / len(points)
    mean_y = sum(p.y for p in points) / len(points)
    cov_xx = sum((p.x - mean_x) ** 2 for p in points) / len(points)
    cov_yy = sum((p.y - mean_y) ** 2 for p in points) / len(points)
    cov_xy = sum((p.x - mean_x) * (p.y - mean_y) for p in points) / len(points)
    if cov_xx == cov_yy and cov_xy == 0:
        return 0.0
    return 0.5 * math.atan2(2 * cov_xy, cov_xx - cov_yy)


def _scanline_positions(min_y: float, max_y: float, spacing: float) -> List[float]:
    if spacing <= 0:
        raise ValueError("Line spacing must be positive.")
    if max_y - min_y <= spacing:
        return [(min_y + max_y) / 2.0]
    positions: List[float] = []
    y = min_y + spacing / 2.0
    while y <= max_y - spacing / 2.0 + 1e-6:
        positions.append(y)
        y += spacing
    if not positions:
        positions = [(min_y + max_y) / 2.0]
    return positions


def _scanline_intersections(polygon: List[XY], y: float) -> List[Tuple[float, float]]:
    xs: List[float] = []
    for i in range(len(polygon) - 1):
        p1 = polygon[i]
        p2 = polygon[i + 1]
        if p1.y == p2.y:
            continue
        if y < min(p1.y, p2.y) or y >= max(p1.y, p2.y):
            continue
        x = p1.x + (y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y)
        xs.append(x)
    xs.sort()
    intersections = []
    for i in range(0, len(xs) - 1, 2):
        intersections.append((xs[i], xs[i + 1]))
    return intersections


