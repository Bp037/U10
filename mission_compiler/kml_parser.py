"""KML/KMZ parsing for LineString or Polygon."""

from __future__ import annotations

import io
import zipfile
from typing import List, Optional
import xml.etree.ElementTree as ET

from .models import InputGeometry, LatLon


class KmlParseError(ValueError):
    pass


def _parse_coordinates(text: str) -> List[LatLon]:
    coords: List[LatLon] = []
    if not text:
        return coords
    for raw in text.strip().split():
        parts = raw.split(",")
        if len(parts) < 2:
            continue
        lon = float(parts[0])
        lat = float(parts[1])
        coords.append(LatLon(lat=lat, lon=lon))
    return coords


def _first_text(root: ET.Element, path: str) -> Optional[str]:
    element = root.find(path)
    if element is None:
        return None
    return element.text


def parse_kml_bytes(data: bytes) -> InputGeometry:
    try:
        root = ET.fromstring(data.decode("utf-8"))
    except UnicodeDecodeError:
        root = ET.fromstring(data.decode("utf-8", errors="ignore"))

    name = _first_text(root, ".//{*}Placemark/{*}name")

    line_strings = root.findall(".//{*}LineString")
    if line_strings:
        coords_el = line_strings[0].find(".//{*}coordinates")
        coords = _parse_coordinates(coords_el.text if coords_el is not None else "")
        if len(coords) < 2:
            raise KmlParseError("LineString must contain at least two coordinates.")
        return InputGeometry(geometry_type="LineString", coordinates=coords, name=name)

    polygons = root.findall(".//{*}Polygon")
    if polygons:
        coords_el = polygons[0].find(".//{*}outerBoundaryIs/{*}LinearRing/{*}coordinates")
        if coords_el is None:
            coords_el = polygons[0].find(".//{*}coordinates")
        coords = _parse_coordinates(coords_el.text if coords_el is not None else "")
        if len(coords) < 3:
            raise KmlParseError("Polygon must contain at least three coordinates.")
        return InputGeometry(geometry_type="Polygon", coordinates=coords, name=name)

    raise KmlParseError("No LineString or Polygon found in KML.")


def parse_kml_or_kmz(data: bytes, filename: str) -> InputGeometry:
    lower = filename.lower()
    if lower.endswith(".kml"):
        return parse_kml_bytes(data)
    if lower.endswith(".kmz"):
        return parse_kmz_bytes(data)
    raise KmlParseError("Unsupported file type. Upload a KML or KMZ.")


def parse_kmz_bytes(data: bytes) -> InputGeometry:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        kml_names = [name for name in zf.namelist() if name.lower().endswith(".kml")]
        if not kml_names:
            raise KmlParseError("KMZ does not contain a KML file.")
        with zf.open(kml_names[0]) as kml_file:
            return parse_kml_bytes(kml_file.read())
