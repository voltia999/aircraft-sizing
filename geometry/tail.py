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
    """
    aileron_chord: float = AILERON_CHORD_RATIO
    aileron_span: tuple = AILERON_SPAN
    elevator_chord: float = ELEVATOR_CHORD_RATIO
    rudder_chord: float = RUDDER_CHORD_RATIO


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
    taper = wing["c_tip"] / wing["c_root"]
    aileron_share = span_area_fraction(taper, *ratios.aileron_span)
    return {
        "ailerons": ratios.aileron_chord * aileron_share * wing["S"],
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
    arm = tail_arm(fuselage_length, coeffs)
    s_ht = horizontal_tail_area(wing["MAC"], wing["S"], arm, coeffs.c_ht)
    s_vt = vertical_tail_area(wing["b"], wing["S"], arm, coeffs.c_vt)
    return {
        "arm": arm, "s_ht": s_ht, "s_vt": s_vt,
        "controls": control_surfaces(wing, s_ht, s_vt, ratios),
    }

