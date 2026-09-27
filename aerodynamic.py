from data import Mission, Aerodynamics
import numpy as np

from ambiance import Atmosphere


def cruise_density(mission: Mission) -> float:
    return float(Atmosphere(mission.altitude).density[0])

def velocity_rel(mission: Mission) -> float:
    return mission.mach * float(Atmosphere(mission.altitude).speed_of_sound[0])

def ld_max(aero:Aerodynamics ) -> float:
    return aero.k_ld * np.sqrt(aero.AR / aero.swet_sref)

def ld_cruise(aero:Aerodynamics) -> float:
    return 0.866 * ld_max(aero)

def sweep_le(aero:Aerodynamics) -> float:
    return np.arctan(np.tan(aero.sweep_c4) + (1 - aero.taper_ratio) / (aero.AR * (1 + aero.taper_ratio)))

def oswald(aero:Aerodynamics) -> float:
    e = 1 - 0.045 * aero.AR ** 0.68
    if np.rad2deg(sweep_le(aero)) > 30.0:
        return 4.61 * e * np.cos(sweep_le(aero)) ** 0.15 - 3.1
    return 1.78 * e - 0.64

def cd0(aero:Aerodynamics) -> float:
    return aero.cfe * aero.swet_sref

def k(aero:Aerodynamics) -> float:
    return 1 / (np.pi * aero.AR * oswald(aero))
