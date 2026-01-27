"""Build a minimal WPML file for DJI Pilot 2."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from typing import List

from .models import Waypoint


def build_wpml(
    waypoints: List[Waypoint],
    speed_mps: float,
    takeoff_security_height_m: float,
) -> str:
    root = ET.Element("wpml", {"xmlns": "http://www.dji.com/wpmz/1.0.0"})
    mission = ET.SubElement(root, "mission")
    mission_config = ET.SubElement(mission, "missionConfig")
    ET.SubElement(mission_config, "missionType").text = "waypoint"
    ET.SubElement(mission_config, "takeoffSecurityHeight").text = _fmt(takeoff_security_height_m)
    ET.SubElement(mission_config, "globalTransitionalSpeed").text = _fmt(speed_mps)
    ET.SubElement(mission_config, "autoFlightSpeed").text = _fmt(speed_mps)
    ET.SubElement(mission_config, "finishAction").text = "goHome"
    ET.SubElement(mission_config, "exitOnRCLost").text = "goHome"

    waypoint_list = ET.SubElement(mission, "waypointList")
    for idx, wp in enumerate(waypoints):
        waypoint = ET.SubElement(waypoint_list, "waypoint")
        ET.SubElement(waypoint, "index").text = str(idx)
        point = ET.SubElement(waypoint, "point")
        ET.SubElement(point, "longitude").text = _fmt(wp.lon)
        ET.SubElement(point, "latitude").text = _fmt(wp.lat)
        ET.SubElement(point, "height").text = _fmt(wp.alt_m)
        ET.SubElement(waypoint, "useGlobalHeight").text = "1"
        ET.SubElement(waypoint, "turnMode").text = "toPointAndStop"
        heading = ET.SubElement(waypoint, "heading")
        ET.SubElement(heading, "mode").text = "followWayline"
        ET.SubElement(heading, "angle").text = "0"
        ET.SubElement(waypoint, "speed").text = _fmt(speed_mps)

    xml_bytes = io.BytesIO()
    ET.ElementTree(root).write(xml_bytes, encoding="UTF-8", xml_declaration=True)
    return xml_bytes.getvalue().decode("utf-8")


def _fmt(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")
