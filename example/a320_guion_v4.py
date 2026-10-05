"""150-seat narrow-body of the guion V4 (Raymer 7th edition).

Inputs follow docs/Dimensionamiento_preliminar_aeronave_Raymer_V4.pdf; section
and equation numbers in the comments refer to that PDF. (H) marks an
assumption of the guion, not published data.

The file is both a case and a worked example:

    python main.py guion-v4               # full sizing report of the case
    python example/a320_guion_v4.py       # step by step, code next to the guion
"""

import sys
from math import radians
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.constants import G, NM, KT, HOUR
from core.data import Mission, Aerodynamics, Design, Reference
from methods import aerodynamic, constraints, weight
from geometry import fuselage, tail, wing
from geometry.fuselage import Deck, SeatingZone

NAME = "guion-v4"


def case() -> tuple:
    mission = Mission(
        n_pax=150,                    # 1.3: 12 business + 138 economy
        m_pax=100.0,                  # 3: passenger + carry-on + checked bag
        n_trip=6,                     # 3: 2 pilots + 4 cabin crew (ORO.CC.100)
        m_trip=95.0,                  # 3: (H) crew bag lighter than checked bag
        range=3000 * NM,              # 1.3: 5 556 km
        mach=0.78,
        altitude=11_000,              # FL360, ISA tropopause
        loiter=45 * 60,               # 1.3: 45 min + 6 % reserve
        v_aprox=135 * KT,             # 1.3: (H) approach category C
        F_takeoff=0.970,              # 4.1, Raymer Table 3.2
        F_ascent=0.985,               # 4.1; refined 1.0065 - 0.0325 M (8.9)
        F_landing=0.995,              # 4.1: descent and landing together
        descent=False,                # 4.4: no separate descent fraction
        F_reserve=1.06,               # 4.4
    )

    aero = Aerodynamics(
        AR=9.5,                       # 5: (H) modern transport wing
        swet_sref=6.0,                # 5: (H) Raymer Fig. 3.6
        k_ld=15.5,                    # 5: Raymer 3.4.4, civil jet -> (L/D)max 19.5
        taper_ratio=0.24,             # 8.5: (H)
        sweep_c4=radians(25.0),       # 8.2.1: (H) Lambda_LE ~ 28 deg -> e ~ 0.77
        c_cruise=0.5 / HOUR,          # 4.2: Raymer Table 3.3
        c_loiter=0.4 / HOUR,          # 4.3
        cfe=0.0026,                   # 5: Raymer Table 12.3 -> CD0 = 0.016
    )

    design = Design(
        wing_loading=600.0,           # 8.3: below the ~655 kg/m2 landing limit
        cruise_wing_loading=550.0,    # 8.8: (H) W/S assumed for the cruise polar
        thrust_to_weight=0.30,        # 8.6: OEI climb above statistical 0.277
        n_engines=2,
        max_mach=0.82,                # 1.3: max operating Mach
        cl_max_landing=2.8,           # 8.1: (H) slats + flaps
        mlw_fraction=0.85,            # 8.1
        vref_factor=1.23,             # 8.1: CS-25
        k_vs=1.0,                     # 6: fixed sweep
        raymer_edition=7,
        decks=_decks(),
        fuselage={"diameter": 3.95,   # 9.1: LD3-45 hold
                  "nose": 4.0,        # 9.2, Table 5
                  "tailcone": 5.0},
        tail_arm_fraction=0.50,       # 10.1: L_HT = L_VT ~ 0.5 Lf
        tail_arm_length="statistical",  # 9.2.1: Lf from Table 6.3 for the tail
    )

    reference = Reference(
        name="guion V4 (segment reference)",
        mtow=78_000,                  # Table 7
        fuel_capacity=18_700,
        thrust=2 * 110e3,             # Table 7: ~100-120 kN per engine
        wing_area=123.0,
        wingspan=34.0,
        aspect_ratio=9.4,             # note v
        fuselage_length=37.6,
        fuselage_width=3.95,
        s_ht=31.0,
        s_vt=21.5,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Section 9: 2-2 business, 3-3 economy, one aisle (Table 5)."""
    main = Deck(
        name="main",
        zones=[
            SeatingZone("business", n_seats=12, seats_abreast=4, seat_pitch=0.97),
            SeatingZone("economy", n_seats=138, seats_abreast=6, seat_pitch=0.81),
        ],
        aisles=1,
        pax_per_lavatory=50,
    )
    return [main]


# --- worked example ---------------------------------------------------------

def section(title: str) -> None:
    print(f"\n{title}\n{'-' * 66}")

def row(label: str, value: float, guion: float, unit: str = "", fmt: str = ",.3f") -> None:
    error = f"{value / guion - 1:+6.1%}" if guion else ""
    print(f"  {label:<30}{value:>12{fmt}} {unit:<6}{guion:>12{fmt}}  {error}")


def main() -> None:
    mission, aero, design, _ = case()
    print(f"  {'':<30}{'code':>12} {'':<6}{'guion':>12}  error")

    section("3  Crew and payload")
    row("Wpayload", weight.w_payload(mission), 15_000, "kg", ",.0f")
    row("Wcrew", weight.w_crew(mission), 570, "kg", ",.0f")

    section("4-5  Fuel fraction (first order)")
    row("V cruise", aerodynamic.velocity_rel(mission), 230, "m/s", ".1f")
    row("(L/D)max = K_LD sqrt(A/Swet)", aerodynamic.ld_max(aero), 19.5, "", ".2f")
    row("(L/D)cruise = 0.866 (L/D)max", aerodynamic.ld_cruise(aero), 16.9, "", ".2f")
    row("W3/W2 cruise (7)", weight.F_cruise(mission, aero), 0.820)
    row("W4/W3 loiter (9)", weight.F_loiter(mission, aero), 0.985)
    row("Wf/W0 (11)", weight.F_fuel(mission, aero), 0.246)

    section("6-7  Empty fraction and W0 (first order, Table 3.1)")
    first = weight.resolve(mission, aero, design)
    row("W0 (17)", first.w0, 72_000, "kg", ",.0f")
    row("We/W0", first.we_w0, 0.537)
    row("We", first.w_empty, 38_600, "kg", ",.0f")
    row("Wf", first.w_fuel, 17_700, "kg", ",.0f")

    section("8.1-8.6  Wing loading, wing and thrust (first-order W0)")
    row("W/S max landing (19)", constraints.landing_wing_loading(mission, design), 655, "kg/m2", ",.0f")
    row("Oswald e (21)", aerodynamic.oswald(aero), 0.77)
    row("K = 1/(pi A e)", aerodynamic.k(aero), 0.0435, "", ".4f")
    row("W/S cruise optimum (20)", constraints.cruise_wing_loading(mission, aero), 365, "kg/m2", ",.0f")
    w1 = wing.wing_geometry(first.w0, aero, design)
    row("S (23)", w1["S"], 120, "m2", ".1f")
    row("b (24)", w1["b"], 33.7, "m", ".2f")
    row("c_root (25)", w1["c_root"], 5.74, "m", ".2f")
    row("MAC (26)", w1["MAC"], 4.00, "m", ".2f")
    row("T/W statistical (Table 5.3)", constraints.statistical_thrust_to_weight(design), 0.277)
    row("T (28)", design.thrust_to_weight * first.w0 * G / 1e3, 212, "kN", ".0f")

    section("8.7-8.12  Refined sizing")
    row("We/W0 Table 6.1 (30)", weight.F_empty_refined(first.w0, aero, design), 0.55)
    ld_polar = aerodynamic.ld_cruise_refined(aero, mission, design)
    row("L/D polar at W/S = 550", ld_polar, 18.9, "", ".2f")
    row("W/W0 climb, Mach (31)", weight.F_ascent_refined(mission), 0.981)
    refined = weight.resolve(mission, aero, design, refined=True)
    row("W0, code refined", refined.w0, 79_800, "kg", ",.0f")
    print("""
  The code puts the polar L/D straight into Breguet, as Raymer 6.3.7 does.
  The guion multiplies it again by 0.866 and keeps the first-order loiter.
  Rebuilding its fuel fraction from the same functions reproduces its W0:""")

    w0, wf_w0 = guion_refined_w0(mission, aero, design, first.w0)
    row("Wf/W0, guion", wf_w0, 0.255)
    row("W0 (32), guion fuel fraction", w0, 79_800, "kg", ",.0f")

    section("8.12  Wing at the refined W0 of the guion")
    w2 = wing.wing_geometry(w0, aero, design)
    row("S (33)", w2["S"], 133, "m2", ".1f")
    row("b", w2["b"], 35.55, "m", ".2f")
    row("c_root", w2["c_root"], 6.03, "m", ".2f")
    row("MAC", w2["MAC"], 4.21, "m", ".2f")
    row("T per engine (34)", design.thrust_to_weight * w0 * G / design.n_engines / 1e3, 117, "kN", ".0f")

    section("9  Fuselage")
    f = fuselage.fuselage_geometry(design.decks, w0=w0, edition=design.raymer_edition,
                                   **design.fuselage)
    row("Cabin length (Table 5)", f["cabin_length"], 28.45, "m", ".2f")
    row("Lf by cabin (35)", f["length"], 37.5, "m", ".2f")
    row("Fineness Lf/D (36)", f["fineness"], 9.5, "", ".2f")
    row("Lf statistical (Table 6.3)", f["statistical_length"], 40.14, "m", ".2f")
    print("\n  The cabin is 0.95 m longer: lavatories are rounded per class (1 + 3),"
          "\n  the guion uses 3 for the 150 seats.")

    section("10  Empennage (arm from the statistical length)")
    t = tail.tail_geometry(w2, f["statistical_length"],
                           tail.TailCoefficients(arm_fraction=design.tail_arm_fraction))
    row("Tail arm L_HT = L_VT", t["arm"], 20.07, "m", ".2f")
    row("S_HT (39)", t["s_ht"], 27.9, "m2", ".1f")
    row("S_VT (41)", t["s_vt"], 21.2, "m2", ".1f")
    c = t["controls"]
    row("Ailerons", c["ailerons"], 6.6, "m2", ".1f")
    row("Elevator", c["elevator"], 7.0, "m2", ".1f")
    row("Rudder", c["rudder"], 6.8, "m2", ".1f")
    print("\n  Ailerons: the code integrates the 50-90 % semispan band with c_a/c = 0.23"
          "\n  (Raymer Fig. 6.3); the guion takes 5 % of S.")


def guion_refined_w0(mission, aero, design, w0_initial: float) -> tuple:
    """W0 and Wf/W0 of guion 8.11-8.12: polar L/D times 0.866, first-order loiter."""
    ld = 0.866 * aerodynamic.ld_cruise_refined(aero, mission, design)
    start = mission.F_takeoff * weight.F_ascent_refined(mission)
    w_x = (start * weight.breguet_cruise(mission, aero, ld)
           * weight.F_loiter(mission, aero) * mission.F_landing)
    wf_w0 = mission.F_reserve * (1 - w_x)
    w0 = w0_initial
    for _ in range(100):
        new = weight.w_fixed(mission) / (1 - wf_w0 - weight.F_empty_refined(w0, aero, design))
        if abs(new - w0) < 1e-2:
            break
        w0 = new
    return new, wf_w0


if __name__ == "__main__":
    main()
