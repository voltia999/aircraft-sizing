"""Airbus A300B4-200: mission requirements and assumptions.

The first twin-aisle twinjet, with CF6-50 high-bypass turbofans and a
three-person flight deck. Inside the Jane's 1976 sample used by Raymer.

Reference figures from memory of public Airbus data: verify against the
EASA type certificate data sheet (A.172) before quoting them.
"""

from math import radians

from constants import NM, KT, HOUR
from data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone


def case() -> tuple:
    mission = Mission(
        n_pax=251,                    # 26 first + 225 economy (2-class)
        n_trip=11,                    # 2 pilots + flight engineer + 8 cabin crew (H)
        range=2900 * NM,              # (H) range with 2-class payload
        mach=0.78,
        altitude=10_058,              # FL330
        loiter=45 * 60,
        v_aprox=135 * KT,             # (H)
    )

    aero = Aerodynamics(
        AR=7.73,                      # 44.84^2 / 260
        swet_sref=6.0,                # (H) Raymer Fig. 3.6
        taper_ratio=0.30,             # (H)
        sweep_c4=radians(28.0),
        c_cruise=0.5 / HOUR,          # Raymer Table 3.3, high-bypass turbofan
        c_loiter=0.4 / HOUR,
    )

    design = Design(
        wing_loading=630.0,           # (H) close to the real 635 kg/m2
        thrust_to_weight=0.28,        # (H) real 2 x 227 kN / MTOW = 0.280
        n_engines=2,
        max_mach=0.82,                # (H)
        cl_max_landing=2.6,           # (H) Fowler flaps + slats
        mlw_fraction=0.81,            # (H) 134 000 / 165 000
        max_span=52.0,                # ICAO code D box
        decks=_decks(),
    )

    reference = Reference(
        name="A300B4-200",
        mtow=165_000, oew=88_500,
        wing_area=260.0, wingspan=44.84,
        fuselage_length=53.62,
        thrust=2 * 227e3,             # CF6-50C, 51 000 lbf
        aspect_ratio=7.73,
        fuselage_width=5.64,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Single deck, two classes, twin aisle, 8 abreast in economy (2-4-2)."""
    main = Deck(
        name="main",
        zones=[
            SeatingZone("first", n_seats=26, seats_abreast=6, seat_pitch=0.97,
                        pax_per_lavatory=20),
            SeatingZone("economy", n_seats=225, seats_abreast=8, seat_pitch=0.86),
        ],
        cabin_height=2.30,
        floor_thickness=0.25,
    )
    return [main]
