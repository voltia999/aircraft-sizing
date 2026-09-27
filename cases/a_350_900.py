"""Airbus A350-900: mission requirements and assumptions.

Long-range twinjet with a mostly composite airframe (Raymer suggests
multiplying the empty-weight fraction by about 0.95 for composites; not
applied here). Mission data follow the earlier desing_a350.py script.

Reference figures from memory of public Airbus data: verify against the
EASA type certificate data sheet (A.151) before quoting them.
"""

from math import radians

from constants import NM, KT, HOUR
from data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone


def case() -> tuple:
    mission = Mission(
        n_pax=325,                    # 48 business + 277 economy (2-class)
        n_trip=16,                    # as in desing_a350.py
        range=8500 * NM,              # 15 740 km, as in desing_a350.py
        mach=0.85,
        altitude=11_000,              # FL360
        loiter=45 * 60,
        v_aprox=140 * KT,             # 72 m/s, as in desing_a350.py
    )

    aero = Aerodynamics(
        AR=9.49,                      # 64.75^2 / 442
        swet_sref=6.0,                # Raymer Fig. 3.6
        taper_ratio=0.22,             # (H)
        sweep_c4=radians(31.9),
        c_cruise=0.5 / HOUR,          # Raymer Table 3.3, high-bypass turbofan
        c_loiter=0.4 / HOUR,
    )

    design = Design(
        wing_loading=640.0,           # (H) close to the real 640 kg/m2
        thrust_to_weight=0.27,        # (H) real 2 x 374 kN / MTOW = 0.270
        n_engines=2,
        max_mach=0.89,
        cl_max_landing=2.5,           # as in desing_a350.py
        mlw_fraction=0.73,            # (H) 207 000 / 283 000
        max_span=65.0,                # ICAO code E box
        decks=_decks(),
    )

    reference = Reference(
        name="A350-900",
        mtow=283_000, oew=142_400,
        wing_area=442.0, wingspan=64.75,
        fuselage_length=66.80,
        thrust=2 * 374.5e3,           # Trent XWB-84, 84 200 lbf
        aspect_ratio=9.49,
        fuselage_width=5.96,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Single deck, two classes, twin aisle, 9 abreast in economy (3-3-3)."""
    main = Deck(
        name="main",
        zones=[
            SeatingZone("business", n_seats=48, seats_abreast=4, seat_pitch=1.52,
                        pax_per_lavatory=20),
            SeatingZone("economy", n_seats=277, seats_abreast=9, seat_pitch=0.81),
        ],
        cabin_height=2.30,
        floor_thickness=0.25,
    )
    return [main]
