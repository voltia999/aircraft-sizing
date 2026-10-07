"""Loiter with the polar, Raymer control surface sizing and the Oswald range check.

Expected values are worked by hand from Raymer 6.3.8, 6.6 (Fig. 6.3, Table 6.5)
and 12.6.1 for the guion's aircraft (A = 9.5, e = 0.77, CD0 = 0.0156).
"""

from dataclasses import replace

import numpy as np
import pytest

from methods import aerodynamic, weight
from core.data import Mission, Aerodynamics
from geometry import tail

REL = 1e-3


@pytest.fixture
def aero():
    return Aerodynamics(AR=9.5, swet_sref=6.0, taper_ratio=0.24,
                        sweep_c4=np.radians(25.0), cfe=0.0026, c_loiter=0.4 / 3600)


@pytest.fixture
def mission():
    return Mission(n_pax=150, loiter=45 * 60)


def test_ld_max_polar(aero):
    """1 / (2 sqrt(0.0156 * 0.04353)) = 19.19."""
    assert aerodynamic.ld_max_polar(aero) == pytest.approx(19.19, rel=REL)


def test_loiter_first_order_unchanged(mission, aero):
    """First order still uses eq. 3.12: (L/D)max = 15.5 sqrt(9.5/6) = 19.5."""
    expected = np.exp(-2700 * 0.4 / 3600 / 19.504)
    assert weight.F_loiter(mission, aero) == pytest.approx(expected, rel=1e-6)


def test_loiter_refined_uses_polar(mission, aero):
    expected = np.exp(-2700 * 0.4 / 3600 / aerodynamic.ld_max_polar(aero))
    assert weight.F_loiter(mission, aero, refined=True) == pytest.approx(expected, rel=1e-9)


def test_span_area_fraction():
    """lambda = 0.24, eta 0.5-0.9: (0.5922 - 0.4050) / 0.62 = 0.302."""
    assert tail.span_area_fraction(0.24, 0.5, 0.9) == pytest.approx(0.3019, rel=REL)
    assert tail.span_area_fraction(0.24, 0.0, 1.0) == pytest.approx(1.0)


def test_control_surfaces_raymer():
    """Ailerons 0.23 * 0.302 * 120 = 8.33 m2; elevator 0.25 * 32; rudder 0.32 * 24.3."""
    wing = {"S": 120, "c_root": 5.73, "c_tip": 5.73 * 0.24}
    c = tail.control_surfaces(wing, 32.0, 24.3)
    assert c["ailerons"] == pytest.approx(8.33, rel=REL)
    assert c["elevator"] == pytest.approx(8.0, rel=REL)
    assert c["rudder"] == pytest.approx(7.776, rel=REL)


def test_oswald_range(aero):
    assert aerodynamic.oswald_in_typical_range(aero)                 # e = 0.770
    swept = Aerodynamics(AR=7.53, taper_ratio=0.22, sweep_c4=np.radians(33.5))
    assert not aerodynamic.oswald_in_typical_range(swept)            # e = 0.567


def test_oswald_fixed(aero):
    """A fixed e replaces the correlation and reaches K."""
    fixed = replace(aero, oswald=0.80)
    assert aerodynamic.oswald(fixed) == 0.80
    assert aerodynamic.k(fixed) == pytest.approx(1 / (np.pi * aero.AR * 0.80))
