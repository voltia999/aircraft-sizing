"""Regression against docs/Dimensionamiento_preliminar_aeronave_Raymer_V4.pdf.

Inputs come from example/a320_guion_v4.py, so the worked example and these
checks cannot drift apart. Expected values are the ones printed in the PDF,
which rounds to about three significant figures: 1 % relative tolerance.
Equation and section numbers refer to the PDF.
"""

import pytest

import aerodynamic
import constraints
import weight
from geometry import fuselage, tail, wing
from main import CASES, run

REL = 0.01
GUION_W0_REFINED = 79_800


@pytest.fixture
def inputs():
    mission, aero, design, _ = CASES["guion-v4"]()
    return mission, aero, design


@pytest.fixture
def example():
    """The worked example module, for the guion's own refined fuel fraction."""
    import importlib.util
    from main import ROOT
    path = ROOT / "example" / "a320_guion_v4.py"
    spec = importlib.util.spec_from_file_location("a320_guion_v4", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- first order: sections 3-8.6 --------------------------------------------

def test_fixed_weight(inputs):
    """Eqs. (3)-(4)."""
    mission, _, _ = inputs
    assert weight.w_fixed(mission) == pytest.approx(15_570)


def test_fuel_fraction(inputs):
    """Eqs. (7), (9), (11)."""
    mission, aero, _ = inputs
    assert aerodynamic.ld_max(aero) == pytest.approx(19.5, rel=REL)
    assert weight.F_cruise(mission, aero) == pytest.approx(0.820, rel=REL)
    assert weight.F_loiter(mission, aero) == pytest.approx(0.985, rel=REL)
    assert weight.F_fuel(mission, aero) == pytest.approx(0.246, rel=REL)


def test_first_order_w0(inputs):
    """Eq. (17): W0 = 72 000 kg, We/W0 = 0.537."""
    mission, aero, design = inputs
    result = weight.resolve(mission, aero, design)
    assert result.w0 == pytest.approx(72_000, rel=REL)
    assert result.we_w0 == pytest.approx(0.537, rel=REL)


def test_wing_loading_limits(inputs):
    """Section 8.1 and eqs. (20)-(21). The cruise W/S uses the unrounded K and CD0."""
    mission, aero, design = inputs
    assert constraints.landing_wing_loading(mission, design) == pytest.approx(655, rel=REL)
    assert aerodynamic.oswald(aero) == pytest.approx(0.77, rel=REL)
    assert constraints.cruise_wing_loading(mission, aero) == pytest.approx(365, rel=0.03)


def test_first_order_wing(inputs):
    """Eqs. (23)-(26) at W0 = 72 000 kg."""
    _, aero, design = inputs
    w = wing.wing_geometry(72_000, aero, design)
    assert w["S"] == pytest.approx(120, rel=REL)
    assert w["b"] == pytest.approx(33.7, rel=REL)
    assert w["c_root"] == pytest.approx(5.74, rel=REL)
    assert w["MAC"] == pytest.approx(4.00, rel=REL)


def test_statistical_thrust_to_weight(inputs):
    """Section 8.6: T/W = 0.297 * 0.82^0.350."""
    _, _, design = inputs
    assert constraints.statistical_thrust_to_weight(design) == pytest.approx(0.277, rel=REL)


# --- refined: sections 8.7-8.12 ---------------------------------------------

def test_refined_pieces(inputs):
    """Eqs. (30)-(31) and section 8.8 (the guion rounds CD0 to 0.016: 2 %)."""
    mission, aero, design = inputs
    assert weight.F_empty_refined(72_000, aero, design) == pytest.approx(0.55, rel=REL)
    assert weight.F_ascent_refined(mission) == pytest.approx(0.981, rel=REL)
    assert aerodynamic.ld_cruise_refined(aero, mission, design) == pytest.approx(18.9, rel=0.02)


def test_guion_refined_w0(inputs, example):
    """Eq. (32), with the guion's extra 0.866 on the polar L/D."""
    mission, aero, design = inputs
    w0, wf_w0 = example.guion_refined_w0(mission, aero, design, 72_000)
    assert wf_w0 == pytest.approx(0.255, rel=REL)
    assert w0 == pytest.approx(GUION_W0_REFINED, rel=REL)


def test_code_refined_w0():
    """Not in the guion: the code's own refined W0 (polar L/D without 0.866).

    Guards against unintended changes; update it if the method changes on purpose.
    """
    assert run("guion-v4")["weights"].w0 == pytest.approx(71_936, rel=1e-3)


# --- geometry at the guion design weight: sections 8.12-10 -----------------

def test_refined_wing(inputs):
    """Section 8.12: S = 133 m2, b = 35.55 m, MAC = 4.21 m."""
    _, aero, design = inputs
    w = wing.wing_geometry(GUION_W0_REFINED, aero, design)
    assert w["S"] == pytest.approx(133, rel=REL)
    assert w["b"] == pytest.approx(35.55, rel=REL)
    assert w["MAC"] == pytest.approx(4.21, rel=REL)


def test_statistical_fuselage_length(inputs):
    """Section 9.2.1: Lf = 0.69 * 79 800^0.36 = 40.14 m."""
    _, _, design = inputs
    assert fuselage.statistical_length(GUION_W0_REFINED, design.raymer_edition) == \
        pytest.approx(40.14, rel=REL)


def test_tail(inputs):
    """Eqs. (39), (41): arm 0.5 * 40.14 = 20.07 m."""
    _, aero, design = inputs
    w = wing.wing_geometry(GUION_W0_REFINED, aero, design)
    lf = fuselage.statistical_length(GUION_W0_REFINED, design.raymer_edition)
    t = tail.tail_geometry(w, lf, tail.TailCoefficients(arm_fraction=design.tail_arm_fraction))
    assert t["arm"] == pytest.approx(20.07, rel=REL)
    assert t["s_ht"] == pytest.approx(27.9, rel=REL)
    assert t["s_vt"] == pytest.approx(21.2, rel=REL)
