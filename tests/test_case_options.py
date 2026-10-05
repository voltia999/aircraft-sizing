"""Design choices that a case can override without touching the method modules.

Each test changes one option from its default and checks that it reaches the
result; the defaults themselves are covered by the guion regressions.
"""

import pytest

from core.data import Design
from geometry import fuselage, tail
from geometry.fuselage import Deck, SeatingZone
from geometry.tail import TailCoefficients, ControlSurfaceRatios
from main import CASES, run


@pytest.fixture
def deck():
    return Deck("main", aisles=1, zones=[
        SeatingZone("business", n_seats=12, seats_abreast=4, seat_pitch=0.97),
        SeatingZone("economy", n_seats=138, seats_abreast=6, seat_pitch=0.81),
    ])


def test_design_defaults_are_raymer_jet_transport():
    design = Design()
    assert design.tail == TailCoefficients(c_ht=1.00, c_vt=0.09, arm_fraction=0.50)
    assert design.controls == ControlSurfaceRatios(
        aileron_chord=0.23, aileron_span=(0.50, 0.90), elevator_chord=0.25, rudder_chord=0.32)


def test_design_instances_do_not_share_tail():
    """Each Design gets its own TailCoefficients (default_factory, not a shared object)."""
    a, b = Design(), Design()
    a.tail.c_ht = 0.6
    assert b.tail.c_ht == 1.00


def test_tail_coefficients_from_the_case(monkeypatch):
    """S_HT scales with c_HT: halving it halves the horizontal tail."""
    base = run("guion-v4")["tail"]
    mission, aero, design, reference = CASES["guion-v4"]()
    design.tail = TailCoefficients(c_ht=0.50, c_vt=0.09, arm_fraction=0.50)
    monkeypatch.setitem(CASES, "guion-v4", lambda: (mission, aero, design, reference))
    changed = run("guion-v4")["tail"]
    assert changed["s_ht"] == pytest.approx(base["s_ht"] / 2)
    assert changed["s_vt"] == pytest.approx(base["s_vt"])


def test_control_ratios_from_the_case(monkeypatch):
    mission, aero, design, reference = CASES["guion-v4"]()
    design.controls = ControlSurfaceRatios(elevator_chord=0.30, rudder_chord=0.30)
    monkeypatch.setitem(CASES, "guion-v4", lambda: (mission, aero, design, reference))
    t = run("guion-v4")["tail"]
    assert t["controls"]["elevator"] == pytest.approx(0.30 * t["s_ht"])
    assert t["controls"]["rudder"] == pytest.approx(0.30 * t["s_vt"])


def test_cabin_standards_per_deck(deck):
    """Longer lavatories and wider aisles change only their own terms."""
    base = fuselage.deck_length(deck)
    deck.lavatory_length = 1.20
    deck.aisle_width = 0.60
    changed = fuselage.deck_length(deck)
    assert changed["lavatories"] == pytest.approx(base["lavatories"] / 0.95 * 1.20)
    assert changed["seating"] == pytest.approx(base["seating"])
    assert fuselage.cabin_width(deck) == pytest.approx(6 * 0.46 + 0.60 + 6 * 0.05)


def test_exit_rule_per_deck(deck):
    """Type C exits (fewer pax per pair) add vestibules."""
    deck.pax_per_exit_pair = 55
    assert fuselage.deck_length(deck)["exits"] == pytest.approx(3 * 1.10)


def test_nose_and_tailcone_contours(deck):
    """Contour angles reach nose_length / tailcone_length through the options."""
    base = fuselage.fuselage_geometry([deck])
    blunt = fuselage.fuselage_geometry([deck], nose_upper_angle=30.0, tailcone_upper_angle=14.0)
    assert blunt["nose"] == pytest.approx(
        fuselage.nose_length(base["section_height"], upper_angle=30.0))
    assert blunt["tailcone"] == pytest.approx(
        fuselage.tailcone_length(base["section_height"], upper_angle=14.0))
    assert blunt["nose"] < base["nose"]


def test_unknown_fuselage_option_is_an_error(deck):
    """A misspelt option must not be silently ignored."""
    with pytest.raises(TypeError, match="nose_angle"):
        fuselage.fuselage_geometry([deck], nose_angle=30.0)
