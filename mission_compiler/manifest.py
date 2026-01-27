"""Manifest generation for compiled missions."""

from __future__ import annotations

from typing import Any, Dict, List

from . import constants
from .models import InputGeometry, MissionPlan
from .units import feet_to_meters, mph_to_mps, mps_to_mph


def build_manifest(
    geometry: InputGeometry,
    plan: MissionPlan,
    effective_footprint_m: float,
    line_spacing_m: float,
    planned_speed_mps: float,
    source_filename: str,
) -> Dict[str, Any]:
    sample_spacing_m = planned_speed_mps / constants.SAMPLE_RATE_HZ
    extension_m = feet_to_meters(constants.MIN_END_EXTENSION_FT)

    notes: List[str] = []
    for note in [
        "Turns are non-data zones.",
        "Geometry uses worst-case AGL for coverage spacing.",
        "Pilot 2 terrain follow and obstacle avoidance remain pilot-configurable.",
    ] + plan.warnings:
        if note not in notes:
            notes.append(note)

    return {
        "generator": {
            "name": "methane-mission-compiler",
        },
        "input": {
            "source_filename": source_filename,
            "geometry_type": geometry.geometry_type,
            "coordinate_count": len(geometry.coordinates),
            "name": geometry.name,
        },
        "sensor_constraints": {
            "sampling_rate_hz": constants.SAMPLE_RATE_HZ,
            "reference_footprint_m": constants.REFERENCE_FOOTPRINT_M,
            "reference_agl_m": constants.REFERENCE_AGL_M,
            "nominal_agl_m": constants.NOMINAL_AGL_M,
            "worst_case_agl_m": constants.WORST_CASE_AGL_M,
            "cross_track_sidelap": constants.CROSS_TRACK_SIDELAP,
            "preferred_speed_mph": constants.PREFERRED_SPEED_MPH,
            "absolute_max_speed_mph": constants.ABSOLUTE_MAX_SPEED_MPH,
            "min_end_extension_ft": constants.MIN_END_EXTENSION_FT,
        },
        "computed": {
            "effective_footprint_m": effective_footprint_m,
            "line_spacing_m": line_spacing_m,
            "min_end_extension_m": extension_m,
            "planned_speed_mps": planned_speed_mps,
            "planned_speed_mph": mps_to_mph(planned_speed_mps),
            "sample_spacing_m": sample_spacing_m,
            "flight_line_count": len(plan.flight_lines),
            "waypoint_count": len(plan.waypoints),
        },
        "notes": notes,
        "assumptions": {
            "line_spacing_based_on_worst_case_agl": True,
            "speed_capped_at_absolute_max": planned_speed_mps < mph_to_mps(constants.PREFERRED_SPEED_MPH),
        },
    }
