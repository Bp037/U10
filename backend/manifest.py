import json

from .constants import *


def write_manifest(path):
    manifest = {
        "sensor": "U10-V5 TDLAS CH4",
        "sampling_rate_hz": SAMPLING_RATE_HZ,
        "reference_agl_m": REFERENCE_AGL_M,
        "worst_case_agl_m": WORST_CASE_AGL_M,
        "footprint_model": "1.0 m @ 100 m (linear)",
        "sidelap_pct": SIDELAP * 100,
        "preferred_speed_mph": PREFERRED_SPEED_MPH,
        "max_speed_mph": MAX_SPEED_MPH,
        "turn_data_excluded": True,
        "terrain_follow_supported": True,
        "validation_method": "CSV GPS + sensor data",
    }

    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
