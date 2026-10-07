"""Tail geometry: empennage sizing by the tail volume coefficient method.

The tail is sized last, because it needs both the wing (MAC, area, span)
and the fuselage (length, which sets the tail arm).

Source: Raymer, Aircraft Design: A Conceptual Approach (6th ed.), chapter 6
(tail volume coefficients, Table 6.4, and tail arm guidance).
"""

from dataclasses import dataclass
from math import atan, degrees, sqrt

# Tail volume coefficients, Raymer Table 6.4 (jet transport)
C_HT_JET_TRANSPORT = 1.00
C_VT_JET_TRANSPORT = 0.09

# Tail arm as a fraction of fuselage length, Raymer chapter 6:
# 0.50-0.55 for wing-mounted engines, 0.45-0.50 for aft-fuselage engines.
ARM_FRACTION_WING_ENGINES = 0.50
ARM_FRACTION_AFT_ENGINES = 0.45

# Volume coefficient reductions, Raymer 6.4 (multiplying factors)
T_TAIL_FACTOR = 0.95          # T-tail: horizontal (clean air) and vertical (end plate)
H_TAIL_FACTOR = 0.95          # H-tail: horizontal
ALL_MOVING_FACTOR = 0.875     # all-moving horizontal tail: 10-15 % smaller
FLY_BY_WIRE_FACTOR = 0.90     # active flight controls: both tails ~10 % smaller
TAIL_CONFIGURATIONS = ("conventional", "t-tail", "h-tail", "v-tail")

# Control surface sizing, Raymer 6.6 (jet transport)
AILERON_CHORD_RATIO = 0.23     # Fig. 6.3, middle of the band for a 0.4 span
AILERON_SPAN = (0.50, 0.90)    # fraction of the semispan, Raymer 6.6
ELEVATOR_CHORD_RATIO = 0.25    # Table 6.5
RUDDER_CHORD_RATIO = 0.32      # Table 6.5


@dataclass
class ControlSurfaceRatios:
    """Chord ratios and aileron span. Defaults are Raymer's jet transport values.

    Control surfaces keep a constant percent chord (Raymer 6.6), so the elevator
    and rudder area ratios equal their chord ratios when they span the whole tail.
    aileron_area_fraction, when set, gives the ailerons directly as a fraction
    of S and overrides aileron_chord and aileron_span.
    """
    aileron_chord: float = AILERON_CHORD_RATIO
    aileron_span: tuple = AILERON_SPAN
    aileron_area_fraction: float | None = None
    elevator_chord: float = ELEVATOR_CHORD_RATIO
    rudder_chord: float = RUDDER_CHORD_RATIO


@dataclass
class TailCoefficients:
    """Volume coefficients and arm. Defaults are Raymer's jet transport values.

    c_ht and c_vt are the Table 6.4 values for a conventional tail; the
    configuration, all_moving and fly_by_wire options apply the reductions of
    Raymer 6.4 on top (see effective_coefficients). A "v-tail" is sized as a
    conventional tail and then merged into two surfaces of the same total area.
    """
    c_ht: float = C_HT_JET_TRANSPORT
    c_vt: float = C_VT_JET_TRANSPORT
    arm_fraction: float = ARM_FRACTION_WING_ENGINES
    configuration: str = "conventional"   # "conventional", "t-tail", "h-tail", "v-tail"
    all_moving: bool = False              # all-moving horizontal tail
    fly_by_wire: bool = False             # active flight control system


def effective_coefficients(coeffs: TailCoefficients) -> tuple:
    """(c_HT, c_VT) after the Raymer 6.4 reductions for configuration and controls."""
    if coeffs.configuration not in TAIL_CONFIGURATIONS:
        raise ValueError(f"Unknown tail configuration '{coeffs.configuration}'; "
                         f"valid: {TAIL_CONFIGURATIONS}")
    c_ht, c_vt = coeffs.c_ht, coeffs.c_vt
    if coeffs.configuration == "t-tail":
        c_ht, c_vt = c_ht * T_TAIL_FACTOR, c_vt * T_TAIL_FACTOR
    elif coeffs.configuration == "h-tail":
        c_ht *= H_TAIL_FACTOR
    if coeffs.all_moving:
        c_ht *= ALL_MOVING_FACTOR
    if coeffs.fly_by_wire:
        c_ht, c_vt = c_ht * FLY_BY_WIRE_FACTOR, c_vt * FLY_BY_WIRE_FACTOR
    return c_ht, c_vt


def v_tail(s_ht: float, s_vt: float) -> dict:
    """V-tail with the same total area as the conventional tail (Raymer 6.4).

    Dihedral = atan(sqrt(S_VT / S_HT)), normally near 45 deg.
    """
    return {"area": s_ht + s_vt, "dihedral": degrees(atan(sqrt(s_vt / s_ht)))}


def tail_arm(fuselage_length: float, coeffs: TailCoefficients) -> float:
    """Distance from the wing quarter-chord to the tail quarter-chord [m]."""
    return coeffs.arm_fraction * fuselage_length


def horizontal_tail_area(mac: float, wing_area: float, arm: float,
                         c_ht: float = C_HT_JET_TRANSPORT) -> float:
    """S_HT = c_HT * MAC * S / L_HT  [m2]."""
    return c_ht * mac * wing_area / arm


def vertical_tail_area(span: float, wing_area: float, arm: float,
                       c_vt: float = C_VT_JET_TRANSPORT) -> float:
    """S_VT = c_VT * b * S / L_VT  [m2].

    Note the reference length is the span, not the MAC: the vertical tail
    counters yawing moments that scale with span (engine-out, for instance).
    """
    return c_vt * span * wing_area / arm


def implied_coefficients(s_ht: float, s_vt: float, mac: float, span: float,
                         wing_area: float, arm: float) -> dict:
    """Reverse the method: volume coefficients of an existing aircraft.

    Useful to compare the design against a real aircraft and see how far
    Raymer's averages sit from current practice.
    """
    return {
        "c_ht": s_ht * arm / (mac * wing_area),
        "c_vt": s_vt * arm / (span * wing_area),
    }


def span_area_fraction(taper_ratio: float, eta_in: float, eta_out: float) -> float:
    """Fraction of a trapezoidal wing's area between two semispan stations.

    With c(eta) = c_root * (1 - (1 - taper) * eta), integrated and normalised.
    """
    def integral(eta):
        return eta - (1 - taper_ratio) * eta ** 2 / 2
    return (integral(eta_out) - integral(eta_in)) / integral(1.0)


def control_surfaces(wing: dict, s_ht: float, s_vt: float,
                     ratios: ControlSurfaceRatios = None) -> dict:
    """Preliminary control surface areas [m2] (Raymer 6.6, Fig. 6.3, Table 6.5).

    `wing` is the dict of geometry.wing.wing_geometry (uses 'S', 'c_root', 'c_tip').
    """
    ratios = ratios or ControlSurfaceRatios()
    if ratios.aileron_area_fraction is not None:
        aileron_fraction = ratios.aileron_area_fraction
    else:
        taper = wing["c_tip"] / wing["c_root"]
        aileron_fraction = ratios.aileron_chord * span_area_fraction(taper, *ratios.aileron_span)
    return {
        "ailerons": aileron_fraction * wing["S"],
        "elevator": ratios.elevator_chord * s_ht,
        "rudder": ratios.rudder_chord * s_vt,
    }


def tail_geometry(wing: dict, fuselage_length: float,
                  coeffs: TailCoefficients = None,
                  ratios: ControlSurfaceRatios = None) -> dict:
    """Full empennage sizing.

    `wing` is the dict returned by geometry.wing.wing_geometry,
    with keys 'S', 'b', 'MAC', 'c_root' and 'c_tip'.
    """
    coeffs = coeffs or TailCoefficients()
    c_ht, c_vt = effective_coefficients(coeffs)
    arm = tail_arm(fuselage_length, coeffs)
    s_ht = horizontal_tail_area(wing["MAC"], wing["S"], arm, c_ht)
    s_vt = vertical_tail_area(wing["b"], wing["S"], arm, c_vt)
    result = {
        "arm": arm, "c_ht": c_ht, "c_vt": c_vt, "s_ht": s_ht, "s_vt": s_vt,
        "controls": control_surfaces(wing, s_ht, s_vt, ratios),
    }
    if coeffs.configuration == "v-tail":
        result["v_tail"] = v_tail(s_ht, s_vt)
    return result

