"""Takeoff, landing and one-engine-out climb constraints (Raymer 5.3, 17.8, App. F).

Expected values are worked by hand from the equations for the 150-seat
aircraft of the guion (A = 9.5, e = 0.77, CD0 = 0.0156, CLmax,L = 2.8).
"""

import numpy as np
import pytest

import constraints
from data import Mission, Aerodynamics, Design

REL = 1e-3


@pytest.fixture
def mission():
    return Mission(n_pax=150)


@pytest.fixture
def aero():
    return Aerodynamics(AR=9.5, swet_sref=6.0, taper_ratio=0.24,
                        sweep_c4=np.radians(25.0), cfe=0.0026)


@pytest.fixture
def design():
    return Design(wing_loading=600.0, thrust_to_weight=0.30, n_engines=2,
                  cl_max_landing=2.8, mlw_fraction=0.85, bypass_ratio=5.5)


def test_cl_max_takeoff_default(design):
    """Raymer 5.3.2: 80 % of the landing value."""
    assert constraints.cl_max_takeoff(design) == pytest.approx(2.24)


def test_second_segment_thrust_to_weight(aero, design):
    """CL = 2.24/1.2^2 = 1.556, CD0 = 0.0356, e = 0.95*0.770:
    T/W = 2 * (0.024 + 0.0229 + 0.0713) = 0.236."""
    required = constraints.climb_thrust_to_weight(aero, design)
    assert required["second segment"] == pytest.approx(0.2363, rel=REL)


def test_landing_go_around_uses_landing_weight(aero, design):
    """All engines, landing flaps and gear, at 0.85 W0."""
    cl = 2.8 / 1.23 ** 2
    d_w = (0.0156 + 0.07 + 0.02) / cl + cl / (np.pi * 9.5 * 0.7698 * 0.90)
    required = constraints.climb_thrust_to_weight(aero, design)
    assert required["landing go-around"] == pytest.approx(0.85 * (0.032 + d_w), rel=REL)


def test_landing_field_length(mission, design):
    """Eq. 5.11: 1.67 * (5 * 510 / 2.8 + 305) = 2030 m."""
    assert constraints.landing_field_length(600.0, mission, design) == pytest.approx(2030.2, rel=REL)


def test_landing_field_round_trip(mission, design):
    mission.landing_field_length = 1800.0
    ws = constraints.landing_field_wing_loading(mission, design)
    assert constraints.landing_field_length(ws, mission, design) == pytest.approx(1800.0)


def test_balanced_field_length(mission, aero, design):
    """Eq. 17.113 at W/S = 600 kg/m2 (122.9 lb/ft2): about 7137 ft."""
    bfl = constraints.balanced_field_length(600.0, mission, aero, design)
    assert bfl == pytest.approx(2175, rel=2e-3)


def test_takeoff_field_round_trip(mission, aero, design):
    mission.takeoff_field_length = 2500.0
    ws = constraints.takeoff_field_wing_loading(mission, aero, design)
    assert constraints.balanced_field_length(ws, mission, aero, design) == pytest.approx(2500.0)


def test_field_limits_only_when_given(mission, aero, design):
    assert set(constraints.wing_loading_limits(mission, aero, design)) == {"approach speed"}
    mission.takeoff_field_length = 2500.0
    mission.landing_field_length = 1800.0
    assert set(constraints.wing_loading_limits(mission, aero, design)) == {
        "approach speed", "landing field", "takeoff field"}


def test_takeoff_field_needs_bypass_ratio(mission, aero, design):
    design.bypass_ratio = None
    mission.takeoff_field_length = 2500.0
    with pytest.raises(ValueError):
        constraints.takeoff_field_wing_loading(mission, aero, design)


def test_high_airport_shortens_allowed_wing_loading(mission, design):
    mission.landing_field_length = 1800.0
    sea_level = constraints.landing_field_wing_loading(mission, design)
    mission.airport_altitude = 1524.0          # 5000 ft, Raymer sigma ~ 0.86 ISA
    assert constraints.landing_field_wing_loading(mission, design) < sea_level
