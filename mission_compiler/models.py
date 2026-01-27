"""Data models for mission compilation."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class LatLon:
    lat: float
    lon: float


@dataclass(frozen=True)
class Line:
    start: LatLon
    end: LatLon


@dataclass(frozen=True)
class Waypoint:
    lat: float
    lon: float
    alt_m: float


@dataclass(frozen=True)
class InputGeometry:
    geometry_type: str  # "LineString" or "Polygon"
    coordinates: List[LatLon]
    name: Optional[str] = None


@dataclass
class MissionPlan:
    geometry_type: str
    waypoints: List[Waypoint]
    flight_lines: List[Line]
    warnings: List[str]
