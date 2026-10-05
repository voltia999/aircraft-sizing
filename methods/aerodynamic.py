from core.data import Mission, Aerodynamics, Design
import numpy as np

from ambiance import Atmosphere
from core.constants import G


def cruise_density(mission: Mission) -> float:
    return float(Atmosphere(mission.altitude).density[0])

def velocity_rel(mission: Mission) -> float:
    return mission.mach * float(Atmosphere(mission.altitude).speed_of_sound[0])

def ld_max(aero:Aerodynamics ) -> float:
    if aero.ld_max is not None:
        return aero.ld_max
    return aero.k_ld * np.sqrt(aero.AR / aero.swet_sref)

def ld_max_polar(aero: Aerodynamics) -> float:
    """(L/D)max of the parabolic polar, at CD0 = K*CL^2."""
    return 1 / (2 * np.sqrt(cd0(aero) * k(aero)))

def ld_cruise(aero:Aerodynamics) -> float:
    return 0.866 * ld_max(aero)

def sweep_le(aero:Aerodynamics) -> float:
    return np.arctan(np.tan(aero.sweep_c4) + (1 - aero.taper_ratio) / (aero.AR * (1 + aero.taper_ratio)))

def oswald(aero:Aerodynamics) -> float:
    e = 1 - 0.045 * aero.AR ** 0.68
    if np.rad2deg(sweep_le(aero)) > 30.0:
        return 4.61 * e * np.cos(sweep_le(aero)) ** 0.15 - 3.1
    return 1.78 * e - 0.64

# Raymer 12.6.1: "typically between 0.7 and 0.85"
OSWALD_TYPICAL_RANGE = (0.70, 0.85)

def oswald_in_typical_range(aero: Aerodynamics) -> bool:
    low, high = OSWALD_TYPICAL_RANGE
    return low <= oswald(aero) <= high

def cd0(aero:Aerodynamics) -> float:
    return aero.cfe * aero.swet_sref

def k(aero:Aerodynamics) -> float:
    return 1 / (np.pi * aero.AR * oswald(aero))

def ld_cruise_refined(aero: Aerodynamics, mission: Mission, design: Design,
                      wing_loading: float = None) -> float:
    """L/D at the cruise CL from the parabolic polar CD = CD0 + K*CL^2 (Raymer 6.13).

    wing_loading [kg/m2] is the actual cruise value; without it, the forced
    design.cruise_wing_loading or, failing that, the takeoff wing loading.
    """
    q = 0.5 * cruise_density(mission) * velocity_rel(mission) ** 2
    ws = (wing_loading or design.cruise_wing_loading or design.wing_loading) * G   # kg/m2 -> N/m2
    return 1 / (q * cd0(aero) / ws + ws * k(aero) / q)
