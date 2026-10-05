"""Raymer adjustments checked against the book (6th ed.).

- Table 6.1 is printed in fps units (W0 in lb, W0/S in lb/ft2) in both editions.
- Composite structure: 0.95 times the statistical empty-weight fraction (ch. 3).
- Tail volume coefficient reductions and V-tail sizing (section 6.4).
"""

from dataclasses import replace
from math import degrees, atan, sqrt, radians

import pytest

from core.constants import LB, FT2
from core.data import Aerodynamics, Design
from geometry import tail
from geometry.tail import TailCoefficients
from methods import weight

WING = {"S": 120.0, "b": 33.75, "MAC": 4.0, "c_root": 5.73, "c_tip": 1.38}


@pytest.fixture
def aero():
    return Aerodynamics(AR=9.5, taper_ratio=0.24, sweep_c4=radians(25.0))


@pytest.mark.parametrize("edition", [6, 7])
def test_table_6_1_uses_fps_units(aero, edition):
    """The metric coefficients reproduce the book's fps formula evaluated in lb and lb/ft2."""
    design = Design(wing_loading=600.0, thrust_to_weight=0.30, max_mach=0.82,
                    raymer_edition=edition)
    w0 = 72_000
    fps = {6: dict(a=0.32, b=0.66, C1=-0.13, C2=0.30, C3=0.06, C4=-0.05, C5=0.05),
           7: dict(a=0.869, b=None, C1=-0.037, C2=0.398, C3=0.100, C4=-0.161, C5=0.050)}[edition]
    product = ((w0 * LB) ** fps["C1"] * aero.AR ** fps["C2"] * 0.30 ** fps["C3"]
               * (600 * LB / FT2) ** fps["C4"] * 0.82 ** fps["C5"])
    book = fps["a"] * product if fps["b"] is None else fps["a"] + fps["b"] * product
    assert weight.F_empty_refined(w0, aero, design) == pytest.approx(book)


def test_composite_factor_first_order():
    assert weight.F_empty(72_000, k_composite=0.95) == pytest.approx(0.95 * weight.F_empty(72_000))


def test_composite_factor_refined(aero):
    metal = Design()
    composite = replace(metal, k_composite=0.95)
    assert weight.F_empty_refined(72_000, aero, composite) == pytest.approx(
        0.95 * weight.F_empty_refined(72_000, aero, metal))


def test_composite_reaches_resolve(aero):
    """Raymer's leverage effect: 5 % less empty weight gives more than 5 % less W0."""
    from core.data import Mission
    mission = Mission(n_pax=150)
    metal = weight.resolve(mission, aero, Design())
    composite = weight.resolve(mission, aero, Design(k_composite=0.95))
    assert composite.w0 / metal.w0 < 0.95


@pytest.mark.parametrize("options, ht_factor, vt_factor", [
    ({}, 1.0, 1.0),
    ({"configuration": "t-tail"}, 0.95, 0.95),
    ({"configuration": "h-tail"}, 0.95, 1.0),
    ({"all_moving": True}, 0.875, 1.0),
    ({"fly_by_wire": True}, 0.90, 0.90),
    ({"configuration": "t-tail", "fly_by_wire": True}, 0.95 * 0.90, 0.95 * 0.90),
])
def test_tail_reductions(options, ht_factor, vt_factor):
    base = tail.tail_geometry(WING, 40.0)
    reduced = tail.tail_geometry(WING, 40.0, TailCoefficients(**options))
    assert reduced["s_ht"] == pytest.approx(base["s_ht"] * ht_factor)
    assert reduced["s_vt"] == pytest.approx(base["s_vt"] * vt_factor)
    assert reduced["c_ht"] == pytest.approx(1.00 * ht_factor)


def test_v_tail_same_total_area():
    """Same total area as the conventional tail; dihedral atan(sqrt(S_VT/S_HT))."""
    t = tail.tail_geometry(WING, 40.0, TailCoefficients(configuration="v-tail"))
    assert t["v_tail"]["area"] == pytest.approx(t["s_ht"] + t["s_vt"])
    assert t["v_tail"]["dihedral"] == pytest.approx(degrees(atan(sqrt(t["s_vt"] / t["s_ht"]))))
    assert "v_tail" not in tail.tail_geometry(WING, 40.0)


def test_unknown_tail_configuration_is_an_error():
    with pytest.raises(ValueError, match="cruciform"):
        tail.tail_geometry(WING, 40.0, TailCoefficients(configuration="cruciform"))
