from constants import G, RHO_SL, LB, FT2, FT, SLUG
from data import Mission, Aerodynamics, Design
from aerodynamic import cd0, k, cruise_density, velocity_rel
import numpy as np

from ambiance import Atmosphere

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

def is_feasible(wing_loading: float, mission: Mission, design: Design) -> bool:
    return wing_loading <= landing_wing_loading(mission, design)

# --- takeoff, landing and one-engine-out climb (Raymer 5.3 and 17.8) --------

# Raymer 5.3.9: drag and span efficiency increments for flaps and gear
DELTA_CD0_TAKEOFF_FLAPS = 0.02
DELTA_CD0_LANDING_FLAPS = 0.07
DELTA_CD0_GEAR = 0.02
E_FACTOR_TAKEOFF_FLAPS = 0.95
E_FACTOR_LANDING_FLAPS = 0.90

# Raymer Table F.4 (FAR 25): minimum climb gradient by number of engines.
# (speed / V_stall, flaps, gear down, one engine out, landing weight, gradients)
CLIMB_SEGMENTS = {
    "first segment":     (1.1,  "takeoff", True,  True,  False, {2: 0.0,   3: 0.003, 4: 0.005}),
    "second segment":    (1.2,  "takeoff", False, True,  False, {2: 0.024, 3: 0.027, 4: 0.030}),
    "approach go-around": (1.4, "takeoff", False, True,  True,  {2: 0.021, 3: 0.024, 4: 0.027}),
    "landing go-around": (1.23, "landing", True,  False, True,  {2: 0.032, 3: 0.032, 4: 0.032}),
}

# Raymer 5.3.5, eq. 5.11: obstacle clearance distance, airliner, 3 deg glideslope
S_A_AIRLINER = 305.0        # m
FAR25_LANDING_FACTOR = 1.67
H_OBSTACLE_FAR25 = 35.0     # ft, Raymer 17.8.4


def density_ratio(mission: Mission) -> float:
    """sigma = rho / rho_SL at the airport altitude (ISA)."""
    return float(Atmosphere(mission.airport_altitude).density[0]) / RHO_SL


def cl_max_takeoff(design: Design) -> float:
    """Raymer 5.3.2: takeoff flaps give about 80 % of the landing CLmax."""
    return design.cl_max_takeoff or 0.8 * design.cl_max_landing


def drag_to_weight(aero: Aerodynamics, cl: float, flaps: str, gear_down: bool) -> float:
    """D/W = CD0/CL + K*CL in steady flight, L = W (Raymer eq. 5.29)."""
    delta = {"takeoff": DELTA_CD0_TAKEOFF_FLAPS, "landing": DELTA_CD0_LANDING_FLAPS}[flaps]
    e_factor = {"takeoff": E_FACTOR_TAKEOFF_FLAPS, "landing": E_FACTOR_LANDING_FLAPS}[flaps]
    cd0_config = cd0(aero) + delta + (DELTA_CD0_GEAR if gear_down else 0.0)
    k_config = k(aero) / e_factor
    return cd0_config / cl + k_config * cl


def climb_thrust_to_weight(aero: Aerodynamics, design: Design) -> dict:
    """Takeoff T/W required by each FAR 25 climb segment (Raymer eq. 5.27-5.30, Table F.4).

    T/W = n/(n-1) * (G + D/W) with one engine out; landing segments are flown at
    the landing weight and ratioed back to takeoff with W_L/W0 (Raymer eq. 5.4).
    Thrust lapse with speed is neglected (sea-level static thrust).
    """
    n = design.n_engines
    required = {}
    for name, (v_ratio, flaps, gear_down, oei, landing, gradients) in CLIMB_SEGMENTS.items():
        cl_max = design.cl_max_landing if flaps == "landing" else cl_max_takeoff(design)
        tw = gradients[min(n, 4)] + drag_to_weight(aero, cl_max / v_ratio ** 2, flaps, gear_down)
        if oei:
            tw *= n / (n - 1)
        if landing:
            tw *= design.mlw_fraction
        required[name] = tw
    return required


def _bfl_terms(aero: Aerodynamics, design: Design) -> tuple:
    """Factors of Raymer eq. 17.113 that do not depend on W/S: BFL = A*(W/S term + h) + B."""
    if design.bypass_ratio is None:
        raise ValueError("La longitud de pista de despegue necesita design.bypass_ratio")
    n = design.n_engines
    cl_to = cl_max_takeoff(design)
    cl_climb = cl_to / 1.2 ** 2                                  # 1.2 V_stall
    d_w = drag_to_weight(aero, cl_climb, "takeoff", gear_down=False)
    gamma_climb = np.arcsin(design.thrust_to_weight * (n - 1) / n - d_w)
    g_margin = gamma_climb - CLIMB_SEGMENTS["second segment"][5][min(n, 4)]
    t_av = 0.75 * design.thrust_to_weight * (5 + design.bypass_ratio) / (4 + design.bypass_ratio)
    u = 0.01 * cl_to + 0.02
    a = 0.863 / (1 + 2.3 * g_margin) * (1 / (t_av - u) + 2.7)
    return a, cl_climb


def balanced_field_length(wing_loading: float, mission: Mission,
                          aero: Aerodynamics, design: Design) -> float:
    """Balanced field length [m] at a takeoff W/S [kg/m2] (Raymer eq. 17.113, fps inside)."""
    a, cl_climb = _bfl_terms(aero, design)
    sigma = density_ratio(mission)
    rho = RHO_SL * sigma * FT ** 3 / SLUG                        # slug/ft3
    ws = wing_loading * LB / FT2                                 # lb/ft2
    bfl = a * (ws / (rho * (G / FT) * cl_climb) + H_OBSTACLE_FAR25) + 655 / np.sqrt(sigma)
    return bfl * FT


def takeoff_field_wing_loading(mission: Mission, aero: Aerodynamics, design: Design) -> float:
    """Maximum takeoff W/S [kg/m2] with BFL <= takeoff field length (eq. 17.113 solved for W/S)."""
    a, cl_climb = _bfl_terms(aero, design)
    sigma = density_ratio(mission)
    rho = RHO_SL * sigma * FT ** 3 / SLUG
    bfl = mission.takeoff_field_length / FT
    ws = ((bfl - 655 / np.sqrt(sigma)) / a - H_OBSTACLE_FAR25) * rho * (G / FT) * cl_climb
    return ws * FT2 / LB


def landing_field_length(wing_loading: float, mission: Mission, design: Design) -> float:
    """FAR 25 landing field length [m] at a takeoff W/S [kg/m2] (Raymer eq. 5.11 x 1.67)."""
    ws_landing = wing_loading * design.mlw_fraction
    s = 5 * ws_landing / (density_ratio(mission) * design.cl_max_landing) + S_A_AIRLINER
    return FAR25_LANDING_FACTOR * s


def landing_field_wing_loading(mission: Mission, design: Design) -> float:
    """Maximum takeoff W/S [kg/m2] for the landing field length (eq. 5.11 solved for W/S)."""
    s = mission.landing_field_length / FAR25_LANDING_FACTOR - S_A_AIRLINER
    ws_landing = s * density_ratio(mission) * design.cl_max_landing / 5
    return ws_landing / design.mlw_fraction


def wing_loading_limits(mission: Mission, aero: Aerodynamics, design: Design) -> dict:
    """Maximum takeoff W/S [kg/m2] from each requirement; field limits only if given."""
    limits = {"approach speed": landing_wing_loading(mission, design)}
    if mission.landing_field_length:
        limits["landing field"] = landing_field_wing_loading(mission, design)
    if mission.takeoff_field_length:
        limits["takeoff field"] = takeoff_field_wing_loading(mission, aero, design)
    return limits
