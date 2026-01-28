# Methane Mission Compiler (DJI Pilot 2 / M350)

Private, web-based mission compiler for DJI Pilot 2 optimized for a methane
TDLAS sensor (U10-V5). The compiler ingests a KML/KMZ LineString centerline,
builds methane-aware flight lines, and outputs a DJI-compatible WPML mission.

## Features (MVP)

- FastAPI backend with `/compile` endpoint
- Simple HTML upload/download frontend (no auth)
- KML or KMZ parsing (LineString centerline)
- Methane sensor physics locked to provided constants
- Output ZIP with:
  - `mission.wpml`
  - `mission_manifest.json`

## Quick Start

```bash
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` and upload a KML/KMZ file.

### Curl example

```bash
curl -X POST \
  -F "file=@path/to/mission.kml" \
  http://localhost:8000/compile \
  -o mission.zip
```

## Notes

- Flight lines use worst-case AGL footprint spacing (95 m).
- MVP generates three lines (left, center, right) from the centerline.
- Turns are considered non-data zones.
- WPML output is intentionally minimal to maximize DJI Pilot 2 import success.