from data import Mission, Aerodynamics, Design
from aerodynamic import velocity_rel, ld_max, ld_cruise, ld_cruise_refined
from results import Result
import numpy as np

from constants import LB, FT2

# Raymer Table 3.1, jet transport (metric), by edition: We/W0 = a * W0^C
TABLE_3_1 = {6: {"a": 0.97, "C": -0.06},
             7: {"a": 1.202, "C": -0.072}}

# Raymer Table 6.1, jet transport (metric: W0 in kg, W0/S in kg/m2), by edition.
# 6th: We/W0 = a + b * W0^C1 * A^C2 * (T/W)^C3 * (W0/S)^C4 * Mmax^C5
# 7th: We/W0 = a * W0^C1 * A^C2 * (T/W)^C3 * (W0/S)^C4 * Mmax^C5 (no additive term)
_T61_V7_FPS = {"a": 0.869, "C1": -0.037, "C2": 0.398,
               "C3": 0.100, "C4": -0.161, "C5": 0.050}
TABLE_6_1 = {
    6: {"a": 0.32, "b": 0.66, "C1": -0.13, "C2": 0.30,
        "C3": 0.06, "C4": -0.05, "C5": 0.05},
    # The 7th edition only gives fps: a_mks = a_fps * LB^C1 * (LB/FT2)^C4
    7: {**_T61_V7_FPS, "b": None,
        "a": _T61_V7_FPS["a"] * LB ** _T61_V7_FPS["C1"] * (LB / FT2) ** _T61_V7_FPS["C4"]},
}

def w_payload(mission: Mission) -> float:
    return mission.n_pax * mission.m_pax

def w_crew(mission: Mission) -> float:
    return mission.n_trip * mission.m_trip

def w_fixed(mission: Mission) -> float:
    return w_crew(mission) + w_payload(mission)

def F_cruise(mission: Mission, aero: Aerodynamics, design: Design = None) -> float:
    """Breguet; with a design, L/D from the polar at the cruise CL."""
    ld = ld_cruise_refined(aero, mission, design) if design else ld_cruise(aero)
    return np.exp(- (mission.range * aero.c_cruise) / (velocity_rel(mission) * ld))

def F_loiter(mission: Mission, aero: Aerodynamics) -> float:
    return np.exp((-mission.loiter * aero.c_loiter) / ld_max(aero))

def F_ascent_refined(mission: Mission) -> float:
    """Raymer 6.3.6: climb and acceleration fraction as a function of Mach."""
    return 1.0065 - 0.0325 * mission.mach

def F_fuel(mission: Mission, aero: Aerodynamics, refined: bool = False,
           design: Design = None) -> float:
    f_ascent = F_ascent_refined(mission) if refined else mission.F_ascent
    f_descent = mission.F_descent if mission.descent else 1.0
    w_x = (mission.F_takeoff
            * f_ascent
            * F_cruise(mission, aero, design if refined else None)
            * F_loiter(mission, aero)
            * f_descent
            * mission.F_landing)
    return mission.F_reserve * (1 - w_x)

def F_empty(w0: float, k_vs: float = 1.0, edition: int = 7) -> float:
    """Raymer Table 3.1, jet transport (metric)."""
    t = TABLE_3_1[edition]
    return t["a"] * w0 ** t["C"] * k_vs

def F_empty_refined(w0: float, aero: Aerodynamics, design: Design) -> float:
    """Raymer Table 6.1, jet transport (metric)."""
    t = TABLE_6_1[design.raymer_edition]
    product = (w0 ** t["C1"] * aero.AR ** t["C2"]
               * design.thrust_to_weight ** t["C3"]
               * design.wing_loading ** t["C4"]
               * design.max_mach ** t["C5"])
    if t["b"] is None:
        return t["a"] * product * design.k_vs
    return (t["a"] + t["b"] * product) * design.k_vs

def resolve(mission: Mission, aero: Aerodynamics, design: Design = None,
            refined: bool = False, w0_initial: float = 5e5,
            tol: float = 1e-2, max_iter: int = 1000) -> Result:
    """Iterate W0 = (Wcrew + Wpayload) / (1 - Wf/W0 - We/W0).

    refined=True uses the Mach-dependent climb fraction, the polar cruise L/D
    and Table 6.1 (requires design); otherwise the first-order Table 3.1 fraction.
    """
    if refined and design is None:
        raise ValueError("El calculo refinado necesita un Design")
    k_vs = design.k_vs if design else 1.0
    edition = design.raymer_edition if design else 7

    def empty_fraction(w: float) -> float:
        return F_empty_refined(w, aero, design) if refined else F_empty(w, k_vs, edition)

    w0, hist = w0_initial, []
    wf_w0 = F_fuel(mission, aero, refined, design)
    for _ in range(max_iter):
        we_w0 = empty_fraction(w0)
        denominator  = 1 - wf_w0 - we_w0
        if denominator <= 0:
            raise ValueError("Mision no cerrable: Wf/W0 + We/W0 >= 1")
        new = w_fixed(mission) / denominator
        hist.append((w0, we_w0, new))
        if abs(new - w0) < tol:
            break
        w0 = new
    else:
        raise RuntimeError(f"W0 no converge en {max_iter} iteraciones")

    return Result(w0=new, wf_w0=wf_w0, we_w0=empty_fraction(new), history=hist,
                  case="refined" if refined else "first-order")
