"""Geographic helpers for local tangent plane conversions."""

from dataclasses import dataclass
import math
from typing import Iterable, List, Tuple

from .constants import EARTH_RADIUS_M
from .models import LatLon


@dataclass(frozen=True)
class XY:
    x: float
    y: float


def reference_from_coords(coords: Iterable[LatLon]) -> Tuple[float, float]:
    lats = [c.lat for c in coords]
    lons = [c.lon for c in coords]
    if not lats or not lons:
        raise ValueError("No coordinates to compute reference.")
    return sum(lats) / len(lats), sum(lons) / len(lons)


def latlon_to_xy(lat: float, lon: float, ref_lat: float, ref_lon: float) -> XY:
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    ref_lat_rad = math.radians(ref_lat)
    ref_lon_rad = math.radians(ref_lon)
    x = (lon_rad - ref_lon_rad) * math.cos(ref_lat_rad) * EARTH_RADIUS_M
    y = (lat_rad - ref_lat_rad) * EARTH_RADIUS_M
    return XY(x=x, y=y)


def xy_to_latlon(x: float, y: float, ref_lat: float, ref_lon: float) -> LatLon:
    ref_lat_rad = math.radians(ref_lat)
    ref_lon_rad = math.radians(ref_lon)
    lat = math.degrees(y / EARTH_RADIUS_M + ref_lat_rad)
    lon = math.degrees(x / (EARTH_RADIUS_M * math.cos(ref_lat_rad)) + ref_lon_rad)
    return LatLon(lat=lat, lon=lon)


def coords_to_xy(coords: Iterable[LatLon], ref_lat: float, ref_lon: float) -> List[XY]:
    return [latlon_to_xy(c.lat, c.lon, ref_lat, ref_lon) for c in coords]


def xy_to_coords(points: Iterable[XY], ref_lat: float, ref_lon: float) -> List[LatLon]:
    return [xy_to_latlon(p.x, p.y, ref_lat, ref_lon) for p in points]


def distance(a: XY, b: XY) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)


def extend_line(start: XY, end: XY, extension_m: float) -> Tuple[XY, XY]:
    length = distance(start, end)
    if length <= 0:
        raise ValueError("Cannot extend zero-length line.")
    dx = (end.x - start.x) / length
    dy = (end.y - start.y) / length
    new_start = XY(start.x - dx * extension_m, start.y - dy * extension_m)
    new_end = XY(end.x + dx * extension_m, end.y + dy * extension_m)
    return new_start, new_end


def rotate(point: XY, angle_rad: float) -> XY:
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return XY(
        x=point.x * cos_a - point.y * sin_a,
        y=point.x * sin_a + point.y * cos_a,
    )


def rotate_points(points: Iterable[XY], angle_rad: float) -> List[XY]:
    return [rotate(p, angle_rad) for p in points]
