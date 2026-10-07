"""Regression against Dimensionamiento_preliminar_aeronave_Raymer_V2.pdf.

The guion sizes a 150-seat narrow-body with Raymer's 6th edition methods.
Expected values are the ones printed in the PDF, which rounds to about
three significant figures, so most checks use a 1 % relative tolerance.
Equation and section numbers refer to the PDF.
"""

import numpy as np
import pytest

from methods import aerodynamic, constraints, weight
from core.constants import G, NM, KT
from core.data import Mission, Aerodynamics, Design
from geometry import fuselage, tail, wing
from geometry.fuselage import Deck, SeatingZone

REL = 0.01


@pytest.fixture
def mission():
    """Table 1 of the guion."""
    return Mission(
        n_pax=150, m_pax=100.0,
        n_trip=6, m_trip=95.0,
        range=3000 * NM,
        mach=0.78,
        altitude=11_000,
        loiter=45 * 60,
        v_aprox=135 * KT,
    )


@pytest.fixture
def aero():
    """Section 5 and 8.2.1: A = 9.5, Swet/Sref = 6, K_LD = 15.5."""
    return Aerodynamics(
        AR=9.5, swet_sref=6.0, k_ld=15.5,
        taper_ratio=0.24, sweep_c4=np.radians(25.0),
        c_cruise=0.5 / 3600, c_loiter=0.5 / 3600,
        cfe=0.0026,
    )


@pytest.fixture
def deck():
    """Section 9: 12 business (2-2) + 138 economy (3-3), one aisle."""
    return Deck(
        "main",
        zones=[SeatingZone("business", n_seats=12, seats_abreast=4, seat_pitch=0.97),
               SeatingZone("economy", n_seats=138, seats_abreast=6, seat_pitch=0.81)],
        aisles=1,
        pax_per_lavatory=50,
    )


@pytest.fixture
def design(deck):
    """Sections 8.1-8.5, with the 6th edition tables used by the guion."""
    return Design(
        wing_loading=600.0,
        thrust_to_weight=0.30,
        n_engines=2,
        max_mach=0.82,
        cl_max_landing=2.8,
        mlw_fraction=0.85,
        raymer_edition=6,
        decks=[deck],
    )


# --- sections 3-5: fixed weight, aerodynamics and fuel fraction ------------

def test_fixed_weight(mission):
    """Eqs. (3)-(4): 15 000 kg payload + 570 kg crew."""
    assert weight.w_payload(mission) == pytest.approx(15_000)
    assert weight.w_crew(mission) == pytest.approx(570)
    assert weight.w_fixed(mission) == pytest.approx(15_570)


def test_cruise_speed(mission):
    """Section 4.2: V = 0.78 * 295 = 230 m/s."""
    assert aerodynamic.velocity_rel(mission) == pytest.approx(230, rel=REL)


def test_lift_to_drag(aero):
    """Eqs. (13)-(14): (L/D)max = 19.5, cruise 0.866 * 19.5 = 16.9."""
    assert aerodynamic.ld_max(aero) == pytest.approx(19.5, rel=REL)
    assert aerodynamic.ld_cruise(aero) == pytest.approx(16.9, rel=REL)


def test_cruise_fraction(mission, aero):
    """Eq. (7)."""
    assert weight.F_cruise(mission, aero) == pytest.approx(0.820, rel=REL)


def test_loiter_fraction(mission, aero):
    """Eq. (9): 45 min at (L/D)max."""
    assert weight.F_loiter(mission, aero) == pytest.approx(0.981, rel=REL)


def test_fuel_fraction_first_order(mission, aero):
    """Eqs. (10)-(11): Wx/W0 = 0.757, Wf/W0 = 1.06 (1 - 0.757) = 0.257."""
    assert weight.F_fuel(mission, aero) == pytest.approx(0.257, rel=REL)


# --- sections 6-7: first-order sizing ----------------------------------------

def test_empty_fraction_table_3_1():
    """Eq. (16) at the converged weight."""
    assert weight.F_empty(64_000, edition=6) == pytest.approx(0.500, rel=REL)


def test_first_order_w0(mission, aero, design):
    """Table 3 and eq. (17): W0 = 64 000 kg, We = 32 000 kg, Wf = 16 450 kg."""
    result = weight.resolve(mission, aero, design, refined=False, w0_initial=70_000)
    assert result.w0 == pytest.approx(64_000, rel=REL)
    assert result.we_w0 == pytest.approx(0.500, rel=REL)
    assert result.w_empty == pytest.approx(32_000, rel=REL)
    assert result.w_fuel == pytest.approx(16_450, rel=REL)


def test_sensitivity_to_empty_fraction():
    """Eq. (18): imposing We/W0 = 0.54 gives W0 = 76 700 kg."""
    assert 15_570 / (1 - 0.257 - 0.54) == pytest.approx(76_700, rel=REL)


# --- section 8: wing loading, wing and thrust --------------------------------

def test_landing_wing_loading(mission, design):
    """Section 8.1: 557 kg/m2 at landing, 655 kg/m2 referred to takeoff."""
    ws = constraints.landing_wing_loading(mission, design)
    assert ws == pytest.approx(655, rel=REL)
    assert ws * design.mlw_fraction == pytest.approx(557, rel=REL)


def test_oswald_factor(aero):
    """Section 8.2.1: sweep_LE = 28 deg < 30 deg, straight-wing e = 0.77."""
    assert np.degrees(aerodynamic.sweep_le(aero)) == pytest.approx(28, rel=REL)
    assert aerodynamic.oswald(aero) == pytest.approx(0.77, rel=REL)


def test_cruise_polar(aero):
    """Section 8.2: K = 0.0435, CD0 = 0.016."""
    assert aerodynamic.k(aero) == pytest.approx(0.0435, rel=REL)
    assert aerodynamic.cd0(aero) == pytest.approx(0.016, rel=0.03)


def test_cruise_wing_loading(mission, aero):
    """Section 8.2: ~365 kg/m2 referred to takeoff.

    The guion rounds CL_opt to 0.35 before multiplying, hence the wider band.
    """
    assert constraints.cruise_wing_loading(mission, aero) == pytest.approx(365, rel=0.03)


def test_wing_first_order(aero, design):
    """Eqs. (23)-(26) at W0 = 64 000 kg."""
    w = wing.wing_geometry(64_000, aero, design)
    assert w["S"] == pytest.approx(107, rel=REL)
    assert w["b"] == pytest.approx(31.9, rel=REL)
    assert w["c_root"] == pytest.approx(5.41, rel=REL)
    assert w["c_tip"] == pytest.approx(1.30, rel=REL)
    assert w["MAC"] == pytest.approx(3.77, rel=REL)


def test_statistical_thrust_to_weight(design):
    """Section 8.5: Table 5.3 gives T/W = 0.25 at Mmax = 0.82."""
    assert constraints.statistical_thrust_to_weight(design) == pytest.approx(0.25, rel=REL)


# --- sections 8.6-8.8: refined sizing ----------------------------------------

def test_refined_climb_fraction(mission):
    """Eq. (31): 1.0065 - 0.0325 * 0.78 = 0.981."""
    assert weight.F_ascent_refined(mission) == pytest.approx(0.981, rel=REL)


def test_fuel_fraction_refined(mission, aero):
    """Section 8.7: Wf/W0 = 0.261. The guion refines only the climb fraction and
    keeps the first-order cruise and loiter."""
    w_x = (mission.F_takeoff * weight.F_ascent_refined(mission)
           * weight.F_cruise(mission, aero) * weight.F_loiter(mission, aero)
           * mission.F_descent * mission.F_landing)
    assert mission.F_reserve * (1 - w_x) == pytest.approx(0.261, rel=REL)


@pytest.mark.parametrize("w0, expected", [(64_000, 0.526), (78_000, 0.521)])
def test_empty_fraction_table_6_1(aero, design, w0, expected):
    """Eq. (30) and section 8.6."""
    assert weight.F_empty_refined(w0, aero, design) == pytest.approx(expected, rel=REL)


@pytest.mark.xfail(strict=True, reason="method differs from the guion: mid-cruise W/S, polar loiter and Table 6.1 in fps units (the guion uses kg)")
def test_refined_w0(mission, aero, design):
    """Eq. (32): W0 = 72 000 kg, We = 37 600 kg, Wf = 18 800 kg."""
    result = weight.resolve(mission, aero, design, refined=True)
    assert result.w0 == pytest.approx(72_000, rel=REL)
    assert result.we_w0 == pytest.approx(0.52, rel=REL)
    assert result.w_empty == pytest.approx(37_600, rel=REL)
    assert result.w_fuel == pytest.approx(18_800, rel=REL)


def test_wing_refined(aero, design):
    """Eq. (33) and section 8.8 at W0 = 72 000 kg."""
    w = wing.wing_geometry(72_000, aero, design)
    assert w["S"] == pytest.approx(120, rel=REL)
    assert w["b"] == pytest.approx(33.8, rel=REL)
    assert w["c_root"] == pytest.approx(5.73, rel=REL)
    assert w["c_tip"] == pytest.approx(1.38, rel=REL)
    assert w["MAC"] == pytest.approx(4.00, rel=REL)


def test_thrust_refined(design):
    """Eq. (34): T = 212 kN, 106 kN per engine."""
    thrust = design.thrust_to_weight * 72_000 * G
    assert thrust == pytest.approx(212e3, rel=REL)
    assert thrust / design.n_engines == pytest.approx(106e3, rel=REL)


# --- section 9: fuselage -----------------------------------------------------

def test_cabin_width(deck):
    """Section 9.1: 6 x 0.46 + 0.51 + 0.30 = 3.57 m."""
    assert fuselage.cabin_width(deck) == pytest.approx(3.57, rel=REL)


@pytest.mark.xfail(strict=True, reason="lavatories rounded per zone (4) vs 3 in the guion")
def test_cabin_length(deck):
    """Table 5: 2.90 + 18.70 + 1.80 + 2.85 + 2.20 = 28.45 m.

    The guion sizes 3 lavatories for 150 seats (one per 50); the code rounds
    up per zone (12/50 -> 1, 138/50 -> 3) and gets 4, so this check fails.
    """
    lengths = fuselage.deck_length(deck)
    assert lengths["galleys"] == pytest.approx(1.80, rel=REL)
    assert lengths["exits"] == pytest.approx(2.20, rel=REL)
    assert lengths["lavatories"] == pytest.approx(2.85, rel=REL)
    assert lengths["total"] == pytest.approx(28.45, rel=REL)


@pytest.mark.xfail(strict=True, reason="follows from test_cabin_length: cabin 0.95 m longer")
def test_fuselage_length(deck):
    """Eqs. (35)-(36): 28.45 + 4.0 + 5.0 = 37.5 m, fineness 37.5 / 3.95 = 9.5."""
    f = fuselage.fuselage_geometry([deck], diameter=3.95, nose=4.0, tailcone=5.0)
    assert f["length"] == pytest.approx(37.5, rel=REL)
    assert f["fineness"] == pytest.approx(9.5, rel=REL)


@pytest.mark.parametrize("w0, expected", [(72_000, 35.2), (78_000, 36.4)])
def test_statistical_fuselage_length(w0, expected):
    """Eq. (37): Table 6.3, 0.287 * W0^0.43."""
    assert fuselage.statistical_length(w0, edition=6) == pytest.approx(expected, rel=REL)


# --- section 10: empennage ---------------------------------------------------

def test_horizontal_tail():
    """Eq. (39): 1.00 * 4.00 * 120 / 15.0 = 32.0 m2."""
    assert tail.horizontal_tail_area(4.00, 120, 15.0) == pytest.approx(32.0, rel=REL)


def test_vertical_tail():
    """Eq. (41): 0.09 * 33.8 * 120 / 15.0 = 24.3 m2."""
    assert tail.vertical_tail_area(33.8, 120, 15.0) == pytest.approx(24.3, rel=REL)


def test_control_surfaces():
    """Table 6: 6.0, 9.6 and 7.3 m2 with the guion's 5 % of S and 30 % of each tail.

    Raymer's Fig. 6.3 sizing of the ailerons is in tests/test_controls_loiter.py.
    """
    wing = {"S": 120, "c_root": 5.73, "c_tip": 1.38}
    ratios = tail.ControlSurfaceRatios(aileron_area_fraction=0.05,
                                       elevator_chord=0.30, rudder_chord=0.30)
    c = tail.control_surfaces(wing, 32.0, 24.3, ratios)
    assert c["ailerons"] == pytest.approx(6.0, rel=REL)
    assert c["elevator"] == pytest.approx(9.6, rel=REL)
    assert c["rudder"] == pytest.approx(7.3, rel=REL)
