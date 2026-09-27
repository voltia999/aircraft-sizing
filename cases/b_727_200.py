"""Boeing 727-200 Advanced: mission requirements and assumptions.

Medium-range trijet with aft-mounted low-bypass JT8D engines and a
three-person flight deck. Inside the Jane's 1976 sample used by Raymer.

Reference figures from memory of public Boeing data: verify against the
FAA type certificate data sheet (A3WE) before quoting them.
"""

from math import radians

from constants import NM, KT, HOUR
from data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone


def case() -> tuple:
    mission = Mission(
        n_pax=134,                    # 12 first + 122 economy (2-class)
        n_trip=7,                     # 2 pilots + flight engineer + 4 cabin crew
        range=2550 * NM,              # (H) range with typical 2-class payload
        mach=0.80,
        altitude=10_058,              # FL330
        loiter=45 * 60,
        v_aprox=137 * KT,             # (H)
    )

    aero = Aerodynamics(
        AR=6.86,                      # 32.92^2 / 157.9
        swet_sref=6.0,                # (H) Raymer Fig. 3.6
        taper_ratio=0.30,             # (H)
        sweep_c4=radians(32.0),
        c_cruise=0.8 / HOUR,          # Raymer Table 3.3, low-bypass turbofan
        c_loiter=0.7 / HOUR,
    )

    design = Design(
        wing_loading=600.0,           # (H) close to the real 602 kg/m2
        thrust_to_weight=0.22,        # (H) real 3 x 69 kN / MTOW = 0.222
        n_engines=3,
        max_mach=0.90,
        cl_max_landing=2.8,           # (H) triple-slotted flaps + slats
        mlw_fraction=0.76,            # (H) 72 575 / 95 030
        max_span=36.0,                # ICAO code C box
        decks=_decks(),
    )

    reference = Reference(
        name="727-200 Adv",
        mtow=95_030, oew=46_700,      # 209 500 lb / ~102 900 lb
        wing_area=157.9, wingspan=32.92,
        fuselage_length=46.69,
        thrust=3 * 68.9e3,            # JT8D-15, 15 500 lbf
        aspect_ratio=6.86,
        fuselage_width=3.76,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Single deck, two classes, one aisle, 6 abreast in economy."""
    main = Deck(
        name="main",
        zones=[
            SeatingZone("first", n_seats=12, seats_abreast=4, seat_pitch=0.97,
                        pax_per_lavatory=20),
            SeatingZone("economy", n_seats=122, seats_abreast=6, seat_pitch=0.81,
                        pax_per_lavatory=50),
        ],
        aisles=1,
        cabin_height=2.20,
        floor_thickness=0.20,
    )
    return [main]
