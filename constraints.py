from constants import G, RHO_SL
from data import Mission, Aerodynamics, Design
from aerodynamic import cd0, k, cruise_density, velocity_rel
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

def statistical_thrust_to_weight(design: Design) -> float:
    return 0.267 * design.max_mach ** 0.363

def is_feasible(wing_loading: float, mission: Mission, design: Design) -> bool:
    return wing_loading <= landing_wing_loading(mission, design)
