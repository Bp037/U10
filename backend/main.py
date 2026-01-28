from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import tempfile
import zipfile

from .kml_parser import parse_kml
from .geometry import generate_flight_lines
from .wpml_writer import write_wpml
from .manifest import write_manifest

app = FastAPI(title="U10-V5 Mission Compiler")


@app.post("/compile")
async def compile_mission(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmp:
        input_path = f"{tmp}/{file.filename}"
        with open(input_path, "wb") as f:
            f.write(await file.read())

        geometry = parse_kml(input_path)
        flight_lines = generate_flight_lines(geometry)

        wpml_path = f"{tmp}/mission.wpml"
        manifest_path = f"{tmp}/mission_manifest.json"

        write_wpml(flight_lines, wpml_path)
        write_manifest(manifest_path)

        zip_path = f"{tmp}/U10-V5_Mission.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            z.write(wpml_path, "mission.wpml")
            z.write(manifest_path, "mission_manifest.json")

        return FileResponse(zip_path, filename="U10-V5_Mission.zip")
