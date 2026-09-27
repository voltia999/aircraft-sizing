"""Boeing 707-320B Intercontinental: mission requirements and assumptions.

A 1960s long-range jet transport, inside the Jane's 1976 sample used by
Raymer for Tables 3.1 and 6.1. Low-bypass JT3D turbofans.

Reference figures from memory of public Boeing data: verify against the
FAA type certificate data sheet (4A21) before quoting them.
"""

from math import radians

from constants import NM, KT, HOUR
from data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone


def case() -> tuple:
    mission = Mission(
        n_pax=147,                    # 14 first + 133 economy (2-class)
        n_trip=9,                     # 2 pilots + flight engineer + 6 cabin crew
        range=3700 * NM,              # range with typical 2-class payload
        mach=0.80,
        altitude=10_668,              # FL350
        loiter=45 * 60,
        v_aprox=140 * KT,             # (H)
    )

    aero = Aerodynamics(
        AR=6.96,                      # 44.42^2 / 283.4
        swet_sref=6.0,                # Raymer Fig. 3.6, similar to the 747
        taper_ratio=0.25,             # (H)
        sweep_c4=radians(35.0),
        c_cruise=0.8 / HOUR,          # Raymer Table 3.3, low-bypass turbofan
        c_loiter=0.7 / HOUR,
    )

    design = Design(
        wing_loading=530.0,           # (H) close to the real 534 kg/m2
        thrust_to_weight=0.22,        # (H) real 4 x 80 kN / MTOW = 0.216
        n_engines=4,
        max_mach=0.887,
        cl_max_landing=2.2,           # (H) double-slotted flaps + Krueger
        mlw_fraction=0.65,            # (H)
        max_span=52.0,                # ICAO code D box
        decks=_decks(),
    )

    reference = Reference(
        name="707-320B",
        mtow=151_320, oew=66_400,     # 333 600 lb / 146 400 lb
        wing_area=283.4, wingspan=44.42,
        fuselage_length=46.61,
        fuel_capacity=90_300 * 0.80,  # 23 855 US gal at 0.80 kg/L
        thrust=4 * 80.1e3,            # JT3D-3B, 18 000 lbf
        aspect_ratio=6.96,
        fuselage_width=3.76,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Single deck, two classes, one aisle, 6 abreast in economy."""
    main = Deck(
        name="main",
        zones=[
            SeatingZone("first", n_seats=14, seats_abreast=4, seat_pitch=0.97,
                        pax_per_lavatory=20),
            SeatingZone("economy", n_seats=133, seats_abreast=6, seat_pitch=0.86,
                        pax_per_lavatory=50),
        ],
        aisles=1,
        cabin_height=2.20,
        floor_thickness=0.20,
    )
    return [main]
