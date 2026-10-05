from core.data import Mission, Aerodynamics, Design
from methods.aerodynamic import velocity_rel, ld_max, ld_max_polar, ld_cruise, ld_cruise_refined
from core.results import Result
import numpy as np

from core.constants import LB, FT2

# Raymer Table 3.1, jet transport (metric), by edition: We/W0 = a * W0^C
TABLE_3_1 = {6: {"a": 0.97, "C": -0.06},
             7: {"a": 1.202, "C": -0.072}}

# Raymer Table 6.1, jet transport, by edition. Both editions give it in fps units
# only (W0 in lb, W0/S in lb/ft2); the code uses kg and kg/m2.
# 6th: We/W0 = a + b * W0^C1 * A^C2 * (T/W)^C3 * (W0/S)^C4 * Mmax^C5
# 7th: We/W0 = a * W0^C1 * A^C2 * (T/W)^C3 * (W0/S)^C4 * Mmax^C5 (no additive term)
_T61_V6_FPS = {"a": 0.32, "b": 0.66, "C1": -0.13, "C2": 0.30,
               "C3": 0.06, "C4": -0.05, "C5": 0.05}
_T61_V7_FPS = {"a": 0.869, "C1": -0.037, "C2": 0.398,
               "C3": 0.100, "C4": -0.161, "C5": 0.050}

def _to_metric(coefficient: float, t: dict) -> float:
    """Constant multiplying W0^C1 (W0/S)^C4, from fps to kg: k * LB^C1 * (LB/FT2)^C4."""
    return coefficient * LB ** t["C1"] * (LB / FT2) ** t["C4"]

TABLE_6_1 = {
    6: {**_T61_V6_FPS, "b": _to_metric(_T61_V6_FPS["b"], _T61_V6_FPS)},
    7: {**_T61_V7_FPS, "b": None, "a": _to_metric(_T61_V7_FPS["a"], _T61_V7_FPS)},
}

def w_payload(mission: Mission) -> float:
    return mission.n_pax * mission.m_pax

def w_crew(mission: Mission) -> float:
    return mission.n_trip * mission.m_trip

def w_fixed(mission: Mission) -> float:
    return w_crew(mission) + w_payload(mission)

def breguet_cruise(mission: Mission, aero: Aerodynamics, ld: float) -> float:
    """Raymer eq. 6.11, jet."""
    return np.exp(- (mission.range * aero.c_cruise) / (velocity_rel(mission) * ld))

def mid_cruise_wing_loading(mission: Mission, aero: Aerodynamics, design: Design,
                            start_of_cruise: float, tol: float = 1e-9) -> float:
    """Actual W/S at mid-cruise [kg/m2] (Raymer note to eq. 6.13 and 12.5.10).

    (W/S)_mid = (W0/S) * start_of_cruise * (1 + F_cruise) / 2, iterated because
    F_cruise depends on the L/D at that W/S. A forced design.cruise_wing_loading
    takes precedence.
    """
    if design.cruise_wing_loading:
        return design.cruise_wing_loading
    ws_start = design.wing_loading * start_of_cruise
    f = 1.0
    for _ in range(100):
        ws = ws_start * (1 + f) / 2
        f_new = breguet_cruise(mission, aero, ld_cruise_refined(aero, mission, design, ws))
        if abs(f_new - f) < tol:
            break
        f = f_new
    return ws_start * (1 + f_new) / 2

def F_cruise(mission: Mission, aero: Aerodynamics, design: Design = None,
             start_of_cruise: float = 1.0) -> float:
    """Breguet; with a design, L/D from the polar at the mid-cruise W/S.

    start_of_cruise is W/W0 at the beginning of cruise (takeoff x climb).
    """
    if design is None:
        return breguet_cruise(mission, aero, ld_cruise(aero))
    ws = mid_cruise_wing_loading(mission, aero, design, start_of_cruise)
    return breguet_cruise(mission, aero, ld_cruise_refined(aero, mission, design, ws))

def F_loiter(mission: Mission, aero: Aerodynamics, refined: bool = False) -> float:
    """Raymer eq. 6.14, jet loiter at (L/D)max: eq. 3.12 (K_LD), or the polar if refined."""
    ld = ld_max_polar(aero) if refined else ld_max(aero)
    return np.exp((-mission.loiter * aero.c_loiter) / ld)

def F_ascent_refined(mission: Mission) -> float:
    """Raymer 6.3.6: climb and acceleration fraction as a function of Mach."""
    return 1.0065 - 0.0325 * mission.mach

def F_fuel(mission: Mission, aero: Aerodynamics, refined: bool = False,
           design: Design = None) -> float:
    f_ascent = F_ascent_refined(mission) if refined else mission.F_ascent
    f_descent = mission.F_descent if mission.descent else 1.0
    w_x = (mission.F_takeoff
            * f_ascent
            * F_cruise(mission, aero, design if refined else None,
                       mission.F_takeoff * f_ascent)
            * F_loiter(mission, aero, refined)
            * f_descent
            * mission.F_landing)
    return mission.F_reserve * (1 - w_x)

def F_empty(w0: float, k_vs: float = 1.0, edition: int = 7,
            k_composite: float = 1.0) -> float:
    """Raymer Table 3.1, jet transport (metric); k_composite = 0.95 for composites."""
    t = TABLE_3_1[edition]
    return t["a"] * w0 ** t["C"] * k_vs * k_composite

def F_empty_refined(w0: float, aero: Aerodynamics, design: Design) -> float:
    """Raymer Table 6.1, jet transport (metric)."""
    t = TABLE_6_1[design.raymer_edition]
    product = (w0 ** t["C1"] * aero.AR ** t["C2"]
               * design.thrust_to_weight ** t["C3"]
               * design.wing_loading ** t["C4"]
               * design.max_mach ** t["C5"])
    factor = design.k_vs * design.k_composite
    if t["b"] is None:
        return t["a"] * product * factor
    return (t["a"] + t["b"] * product) * factor

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
    k_composite = design.k_composite if design else 1.0
    edition = design.raymer_edition if design else 7

    def empty_fraction(w: float) -> float:
        if refined:
            return F_empty_refined(w, aero, design)
        return F_empty(w, k_vs, edition, k_composite)

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
