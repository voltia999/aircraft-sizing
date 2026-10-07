"""Physical trends: the method responds in the right direction, and by the right
amount where the equation fixes it.

The regressions check one design point; these sweep inputs around the guion V4
aircraft and catch sign errors and wrong exponents that a single point hides.
"""

from dataclasses import replace
from math import radians

import numpy as np
import pytest

from example.a320_guion_v4 import case
from geometry import fuselage, tail, wing
from geometry.fuselage import Deck, SeatingZone
from methods import aerodynamic, constraints, weight


@pytest.fixture
def inputs():
    mission, aero, design, _ = case()
    return mission, aero, design


def increasing(values) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


def decreasing(values) -> bool:
    return all(b < a for a, b in zip(values, values[1:]))


# --- weights -----------------------------------------------------------------

@pytest.mark.parametrize("refined", [False, True])
@pytest.mark.parametrize("field, values", [
    ("range", [2000e3, 4000e3, 6000e3]),
    ("n_pax", [100, 150, 200]),
    ("loiter", [20 * 60, 45 * 60, 60 * 60]),
])
def test_w0_grows_with_mission(inputs, refined, field, values):
    mission, aero, design = inputs
    w0 = [weight.resolve(replace(mission, **{field: v}), aero, design, refined).w0 for v in values]
    assert increasing(w0)


@pytest.mark.parametrize("refined", [False, True])
def test_w0_grows_with_fuel_consumption(inputs, refined):
    mission, aero, design = inputs
    w0 = [weight.resolve(mission, replace(aero, c_cruise=c / 3600), design, refined).w0
          for c in (0.4, 0.5, 0.6)]
    assert increasing(w0)


def test_w0_falls_with_aerodynamic_efficiency(inputs):
    """First order: (L/D)max grows with K_LD, so less fuel and less W0."""
    mission, aero, design = inputs
    w0 = [weight.resolve(mission, replace(aero, k_ld=k), design).w0 for k in (13, 15.5, 18)]
    assert decreasing(w0)


def test_breguet_range_is_exponential(inputs):
    """Twice the range squares the cruise weight fraction."""
    mission, aero, _ = inputs
    single = weight.F_cruise(mission, aero)
    double = weight.F_cruise(replace(mission, range=2 * mission.range), aero)
    assert double == pytest.approx(single ** 2)


def test_payload_growth_factor(inputs):
    """Each extra kg of payload adds more than 1 kg of W0 (fuel and structure to
    carry it), but doubling the payload less than doubles W0, because We/W0
    falls with size."""
    mission, aero, design = inputs
    small = weight.resolve(mission, aero, design)
    big = weight.resolve(replace(mission, n_pax=2 * mission.n_pax), aero, design)
    extra_payload = weight.w_fixed(replace(mission, n_pax=2 * mission.n_pax)) - weight.w_fixed(mission)
    assert big.w0 - small.w0 > extra_payload
    assert big.w0 < 2 * small.w0


@pytest.mark.parametrize("edition", [6, 7])
def test_empty_fraction_falls_with_size(edition):
    """Table 3.1: negative exponent, bigger aircraft are structurally lighter."""
    fractions = [weight.F_empty(w0, edition=edition) for w0 in (20_000, 70_000, 400_000)]
    assert decreasing(fractions)


@pytest.mark.parametrize("field, values, trend", [
    ("AR", [7.5, 9.5, 11.5], increasing),             # C2 > 0: slender wings are heavier
])
def test_refined_empty_fraction_aero(inputs, field, values, trend):
    _, aero, design = inputs
    assert trend([weight.F_empty_refined(72_000, replace(aero, **{field: v}), design)
                  for v in values])


@pytest.mark.parametrize("field, values, trend", [
    ("thrust_to_weight", [0.25, 0.30, 0.35], increasing),   # C3 > 0: bigger engines
    ("wing_loading", [450, 600, 750], decreasing),          # C4 < 0: smaller wing
    ("max_mach", [0.70, 0.82, 0.90], increasing),           # C5 > 0
])
def test_refined_empty_fraction_design(inputs, field, values, trend):
    _, aero, design = inputs
    assert trend([weight.F_empty_refined(72_000, aero, replace(design, **{field: v}))
                  for v in values])


# --- aerodynamics ------------------------------------------------------------

def test_oswald_falls_with_aspect_ratio(inputs):
    """Eq. 12.48 (straight wing): e = 1.78 (1 - 0.045 A^0.68) - 0.64."""
    _, aero, _ = inputs
    assert decreasing([aerodynamic.oswald(replace(aero, AR=a)) for a in (6, 9.5, 12)])


def test_oswald_falls_with_sweep(inputs):
    """Eq. 12.49 (Λ_LE > 30°): the cos(Λ_LE)^0.15 factor falls with sweep."""
    _, aero, _ = inputs
    sweeps = [radians(s) for s in (32, 37, 42)]
    assert decreasing([aerodynamic.oswald(replace(aero, sweep_c4=s)) for s in sweeps])


def test_polar_peaks_at_ld_max(inputs):
    """Swept over W/S, the polar L/D peaks at the (L/D)max of the polar."""
    mission, aero, design = inputs
    ld = [aerodynamic.ld_cruise_refined(aero, mission, design, ws) for ws in np.linspace(200, 900, 701)]
    assert max(ld) == pytest.approx(aerodynamic.ld_max_polar(aero), rel=1e-4)
    assert max(ld) <= aerodynamic.ld_max_polar(aero) * (1 + 1e-12)


# --- wing loading ------------------------------------------------------------

def test_landing_wing_loading_scales(inputs):
    """Eq. 19: W/S proportional to V_approach² and to CL_max."""
    mission, _, design = inputs
    base = constraints.landing_wing_loading(mission, design)
    faster = constraints.landing_wing_loading(replace(mission, v_aprox=1.1 * mission.v_aprox), design)
    more_lift = constraints.landing_wing_loading(mission, replace(design, cl_max_landing=1.2 * design.cl_max_landing))
    assert faster == pytest.approx(1.21 * base)
    assert more_lift == pytest.approx(1.2 * base)


def test_cruise_wing_loading_scales_with_mach(inputs):
    """W/S at the optimum CL is q·CL_opt, and q grows with M²."""
    mission, aero, _ = inputs
    base = constraints.cruise_wing_loading(mission, aero)
    faster = constraints.cruise_wing_loading(replace(mission, mach=0.85), aero)
    assert faster / base == pytest.approx((0.85 / mission.mach) ** 2)


def test_cruise_wing_loading_falls_with_altitude(inputs):
    """At constant Mach, q falls with altitude (lower pressure)."""
    mission, aero, _ = inputs
    assert decreasing([constraints.cruise_wing_loading(replace(mission, altitude=h), aero)
                       for h in (8_000, 10_000, 12_000)])


# --- geometry ----------------------------------------------------------------

def test_wing_area_scales(inputs):
    """S = W0 / (W/S); b = sqrt(A S)."""
    _, aero, design = inputs
    base = wing.wing_geometry(72_000, aero, design)
    heavier = wing.wing_geometry(2 * 72_000, aero, design)
    loaded = wing.wing_geometry(72_000, aero, replace(design, wing_loading=2 * design.wing_loading))
    slender = wing.wing_geometry(72_000, replace(aero, AR=4 * aero.AR), design)
    assert heavier["S"] == pytest.approx(2 * base["S"])
    assert loaded["S"] == pytest.approx(base["S"] / 2)
    assert slender["S"] == pytest.approx(base["S"])
    assert slender["b"] == pytest.approx(2 * base["b"])


def test_tail_area_scales():
    """Eqs. 38 and 40: S_tail proportional to the coefficient, inverse to the arm."""
    assert tail.horizontal_tail_area(4.0, 120, 20.0, c_ht=1.2) == pytest.approx(
        1.2 * tail.horizontal_tail_area(4.0, 120, 20.0, c_ht=1.0))
    assert tail.horizontal_tail_area(4.0, 120, 40.0) == pytest.approx(
        tail.horizontal_tail_area(4.0, 120, 20.0) / 2)
    assert tail.vertical_tail_area(34.0, 120, 40.0) == pytest.approx(
        tail.vertical_tail_area(34.0, 120, 20.0) / 2)


def test_longer_fuselage_smaller_tails(inputs):
    _, aero, design = inputs
    w = wing.wing_geometry(72_000, aero, design)
    s_ht = [tail.tail_geometry(w, lf, design.tail)["s_ht"] for lf in (30, 38, 46)]
    assert decreasing(s_ht)


def _deck(n_seats: int, abreast: int) -> Deck:
    return Deck("main", aisles=1, zones=[
        SeatingZone("economy", n_seats=n_seats, seats_abreast=abreast, seat_pitch=0.81)])


def test_cabin_grows_with_seats():
    assert increasing([fuselage.deck_length(_deck(n, 6))["total"] for n in (120, 150, 180)])


def test_more_seats_abreast_shorter_and_wider_cabin():
    narrow, wide = _deck(150, 5), _deck(150, 6)
    assert fuselage.deck_length(wide)["seating"] < fuselage.deck_length(narrow)["seating"]
    assert fuselage.cabin_width(wide) > fuselage.cabin_width(narrow)
