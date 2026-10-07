from core.constants import G, RHO_SL
from core.data import Mission, Aerodynamics, Design
from methods.aerodynamic import cd0, k, cruise_density, velocity_rel
import numpy as np

def landing_wing_loading(mission: Mission, design: Design) -> float:

    v_stall = mission.v_aprox / design.vref_factor
    ws_landing = 0.5 * RHO_SL * v_stall ** 2 * design.cl_max_landing / G
    return ws_landing / design.mlw_fraction

def cruise_wing_loading(mission: Mission, aero: Aerodynamics,
                        start_of_cruise: float = None) -> float:
    """Takeoff W/S for the optimum cruise CL [kg/m2].

    start_of_cruise defaults to the takeoff and climb fractions of the mission.
    """
    if start_of_cruise is None:
        start_of_cruise = mission.F_takeoff * mission.F_ascent
    cl_opt = np.sqrt(cd0(aero) / (3 * k(aero)))
    q = 0.5 * cruise_density(mission) * velocity_rel(mission) ** 2
    return cl_opt * q / G / start_of_cruise

# Raymer Table 5.3, jet transport, by edition: T/W = a * Mmax^C
TABLE_5_3 = {6: {"a": 0.267, "C": 0.363},
             7: {"a": 0.297, "C": 0.350}}

def statistical_thrust_to_weight(design: Design) -> float:
    t = TABLE_5_3[design.raymer_edition]
    return t["a"] * design.max_mach ** t["C"]
