"""Tail geometry: empennage sizing by the tail volume coefficient method.

The tail is sized last, because it needs both the wing (MAC, area, span)
and the fuselage (length, which sets the tail arm).

Source: Raymer, Aircraft Design: A Conceptual Approach (6th ed.), chapter 6
(tail volume coefficients, Table 6.4, and tail arm guidance).
"""

from dataclasses import dataclass

# Tail volume coefficients, Raymer Table 6.4 (jet transport)
C_HT_JET_TRANSPORT = 1.00
C_VT_JET_TRANSPORT = 0.09

# Tail arm as a fraction of fuselage length, Raymer chapter 6:
# 0.50-0.55 for wing-mounted engines, 0.45-0.50 for aft-fuselage engines.
ARM_FRACTION_WING_ENGINES = 0.50
ARM_FRACTION_AFT_ENGINES = 0.45

# Control surface sizing, conceptual fractions
AILERON_FRACTION = 0.05     # of wing area
ELEVATOR_FRACTION = 0.30    # of horizontal tail area
RUDDER_FRACTION = 0.30      # of vertical tail area


@dataclass
class TailCoefficients:
    """Volume coefficients and arm. Defaults are Raymer's jet transport values.

    Lower coefficients are justified for large fly-by-wire aircraft with
    relaxed static stability (the A380 works at c_ht ~ 0.6-0.7).
    """
    c_ht: float = C_HT_JET_TRANSPORT
    c_vt: float = C_VT_JET_TRANSPORT
    arm_fraction: float = ARM_FRACTION_WING_ENGINES


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


def control_surfaces(wing_area: float, s_ht: float, s_vt: float) -> dict:
    """Preliminary control surface areas [m2]."""
    return {
        "ailerons": AILERON_FRACTION * wing_area,
        "elevator": ELEVATOR_FRACTION * s_ht,
        "rudder": RUDDER_FRACTION * s_vt,
    }


def tail_geometry(wing: dict, fuselage_length: float,
                  coeffs: TailCoefficients = None) -> dict:
    """Full empennage sizing.

    `wing` is the dict returned by geometry.wing.wing_geometry,
    with keys 'S', 'b' and 'MAC'.
    """
    coeffs = coeffs or TailCoefficients()
    arm = tail_arm(fuselage_length, coeffs)
    s_ht = horizontal_tail_area(wing["MAC"], wing["S"], arm, coeffs.c_ht)
    s_vt = vertical_tail_area(wing["b"], wing["S"], arm, coeffs.c_vt)
    return {
        "arm": arm, "s_ht": s_ht, "s_vt": s_vt,
        "controls": control_surfaces(wing["S"], s_ht, s_vt),
    }

