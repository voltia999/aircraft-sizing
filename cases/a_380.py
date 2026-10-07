"""Airbus A380-800: mission requirements and design assumptions.

Published example of a case outside the guion: two decks and four engines.
(H) marks an assumption, not published data.

    python main.py a380

Raymer's eq. 12.49 (leading-edge sweep above 30 deg) gives e = 0.57 for this
wing, below the typical 0.70-0.85 band of section 12.6.1, and MTOW ends up
near 1 070 t. The case fixes e = 0.80, mid band.

Design.max_span is not applied yet (see the main README), so the span is not
cut to the 80 m of the ICAO code F box.
"""

from math import radians

from core.constants import KT, HOUR
from core.data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone

NAME = "a380"

def case() -> tuple:
    mission = Mission(
        n_pax=484,                     # three-class layout of _decks()
        n_trip=18,                     # (H) flight and cabin crew
        range=15_200e3,                # 15 200 km (~8 200 NM)
        mach=0.85,
        altitude=10_668,               # FL350
        loiter=20 * 60,
        v_aprox=140 * KT,
    )

    aero = Aerodynamics(
        AR=7.53,                       # span-limited: ICAO code F box
        swet_sref=6,                   # (H) component estimate
        oswald=0.80,                   # (H) mid of Raymer's 0.70-0.85; eq. 12.49 gives 0.57
        taper_ratio=0.22,
        sweep_c4=radians(33.5),
        c_loiter=0.4 / HOUR,           # Raymer Table 3.3, high-bypass turbofan
    )

    design = Design(
        wing_loading=650.0,
        thrust_to_weight=0.25,
        n_engines=4,
        max_mach=0.89,
        cl_max_landing=2.5,            # (H)
        mlw_fraction=0.70,             # long range: MLW well below MTOW
        max_span=79.8,                 # ICAO code F (not applied yet)
        decks=_decks(),
    )

    reference = Reference(
        name="A380-800",
        mtow=560_000, oew=277_000,
        wing_area=845.0, wingspan=79.75,
        fuselage_length=72.72,
        mlw=386_000,
        fuel_capacity=320_000 * 0.80,  # 320 000 L at 0.80 kg/L
        thrust=4 * 310e3,              # Trent 970, 70 000 lbf
        aspect_ratio=7.53,
        fuselage_width=7.14, fuselage_height=8.41,
        cabin_length=49.9,             # main deck
        s_ht=205.6, s_vt=122.3,
    )

    return mission, aero, design, reference

def _decks() -> list:
    """Main deck: first 1-2-1 and economy 3-4-3; upper deck: business 2-2-2 and economy 2-4-2."""
    main = Deck("main",
                zones=[SeatingZone("first", n_seats=12, seats_abreast=4, seat_pitch=2.00, pax_per_lavatory=10),
                       SeatingZone("economy", n_seats=340, seats_abreast=10, seat_pitch=0.81)],
                cabin_height=2.30, floor_thickness=0.25)
    upper = Deck("upper",
                 zones=[SeatingZone("business", n_seats=78, seats_abreast=6, seat_pitch=1.52, pax_per_lavatory=20),
                        SeatingZone("economy", n_seats=54, seats_abreast=8, seat_pitch=0.81)],
                 n_staircases=2, cabin_height=2.10, floor_thickness=0.30)
    return [main, upper]
