from shapely.affinity import translate

from .constants import FOOTPRINT_WORST_CASE_M, SIDELAP


def generate_flight_lines(centerline):
    spacing = FOOTPRINT_WORST_CASE_M * (1 - SIDELAP)

    # MVP: 3-line coverage (left, center, right)
    offsets = [-spacing, 0, spacing]

    lines = []
    for offset in offsets:
        lines.append(translate(centerline, xoff=offset))

    return lines
