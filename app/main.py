"""FastAPI entrypoint for methane mission compiler."""

from __future__ import annotations

import io
import json
import os
import zipfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response

from mission_compiler import constants
from mission_compiler.flight_lines import plan_flight_lines
from mission_compiler.kml_parser import KmlParseError, parse_kml_or_kmz
from mission_compiler.manifest import build_manifest
from mission_compiler.units import feet_to_meters, mph_to_mps
from mission_compiler.wpml_builder import build_wpml

app = FastAPI(title="Methane Mission Compiler", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <html>
      <head>
        <title>Methane Mission Compiler</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 2rem; }
          .card { max-width: 640px; padding: 1rem 1.5rem; border: 1px solid #ddd; border-radius: 8px; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>Methane Mission Compiler</h1>
          <p>Upload a KML or KMZ containing a LineString or Polygon.</p>
          <form action="/compile" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".kml,.kmz" required />
            <button type="submit">Compile Mission</button>
          </form>
          <p>Output: mission.zip containing mission.wpml and mission_manifest.json.</p>
        </div>
      </body>
    </html>
    """


@app.post("/compile")
async def compile_mission(file: UploadFile = File(...)) -> Response:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        geometry = parse_kml_or_kmz(data, file.filename)
    except KmlParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    effective_footprint_m = (
        constants.REFERENCE_FOOTPRINT_M * constants.WORST_CASE_AGL_M / constants.REFERENCE_AGL_M
    )
    line_spacing_m = effective_footprint_m * (1.0 - constants.CROSS_TRACK_SIDELAP)
    extension_m = feet_to_meters(constants.MIN_END_EXTENSION_FT)

    preferred_speed_mps = mph_to_mps(constants.PREFERRED_SPEED_MPH)
    max_speed_mps = mph_to_mps(constants.ABSOLUTE_MAX_SPEED_MPH)
    planned_speed_mps = min(preferred_speed_mps, max_speed_mps)

    try:
        plan = plan_flight_lines(
            geometry=geometry,
            extension_m=extension_m,
            line_spacing_m=line_spacing_m,
            nominal_alt_m=constants.NOMINAL_AGL_M,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    wpml = build_wpml(
        waypoints=plan.waypoints,
        speed_mps=planned_speed_mps,
        takeoff_security_height_m=constants.TAKEOFF_SECURITY_HEIGHT_M,
    )
    manifest = build_manifest(
        geometry=geometry,
        plan=plan,
        effective_footprint_m=effective_footprint_m,
        line_spacing_m=line_spacing_m,
        planned_speed_mps=planned_speed_mps,
        source_filename=file.filename,
    )

    zip_bytes = _build_zip(wpml, manifest)
    filename = _download_name(file.filename)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=zip_bytes, media_type="application/zip", headers=headers)


def _build_zip(wpml: str, manifest: dict) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mission.wpml", wpml)
        zf.writestr("mission_manifest.json", json.dumps(manifest, indent=2))
    return buffer.getvalue()


def _download_name(source_name: str) -> str:
    base, _ = os.path.splitext(os.path.basename(source_name))
    if not base:
        return "mission.zip"
    return f"{base}_mission.zip"
