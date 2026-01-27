"""Unit conversions."""

FT_TO_M = 0.3048
MPH_TO_MPS = 0.44704


def feet_to_meters(feet: float) -> float:
    return feet * FT_TO_M


def meters_to_feet(meters: float) -> float:
    return meters / FT_TO_M


def mph_to_mps(mph: float) -> float:
    return mph * MPH_TO_MPS


def mps_to_mph(mps: float) -> float:
    return mps / MPH_TO_MPS
