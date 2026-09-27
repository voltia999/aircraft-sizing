"""Boeing 747-400: mission requirements and assumptions.

Long-range quadjet with high-bypass turbofans. The upper deck is a short
hump over the forward fuselage, so only the main deck is modelled: it sets
both the length and the section (a full second deck would overstate the
height). The upper-deck seats still count in the payload.

Reference figures from memory of public Boeing data: verify against the
FAA type certificate data sheet (A20WE) before quoting them.
"""

from math import radians

from constants import NM, KT, HOUR
from data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone


def case() -> tuple:
    mission = Mission(
        n_pax=416,                    # Boeing 3-class (32 on the upper deck)
        n_trip=20,                    # 4 pilots + 16 cabin crew (H)
        range=7260 * NM,              # (H) range with 3-class payload
        mach=0.85,
        altitude=10_668,              # FL350
        loiter=45 * 60,
        v_aprox=150 * KT,             # (H)
    )

    aero = Aerodynamics(
        AR=7.67,                      # 64.44^2 / 541.2
        swet_sref=6.0,                # Raymer Fig. 3.6 (747)
        taper_ratio=0.25,             # (H)
        sweep_c4=radians(37.5),
        c_cruise=0.5 / HOUR,          # Raymer Table 3.3, high-bypass turbofan
        c_loiter=0.4 / HOUR,
    )

    design = Design(
        wing_loading=730.0,           # (H) close to the real 733 kg/m2
        thrust_to_weight=0.26,        # (H) real 4 x 252 kN / MTOW = 0.259
        n_engines=4,
        max_mach=0.92,
        cl_max_landing=2.6,           # (H) triple-slotted flaps + Krueger
        mlw_fraction=0.72,            # (H) 285 764 / 396 890
        max_span=65.0,                # ICAO code E box
        decks=_decks(),
    )

    reference = Reference(
        name="747-400",
        mtow=396_890, oew=178_750,    # 875 000 lb / 394 100 lb
        wing_area=541.2, wingspan=64.44,
        fuselage_length=70.66,
        thrust=4 * 252.4e3,           # PW4056, 56 750 lbf
        aspect_ratio=7.67,
        fuselage_width=6.50,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Main deck only, three classes, twin aisle, 10 abreast in economy."""
    main = Deck(
        name="main",
        zones=[
            SeatingZone("first", n_seats=14, seats_abreast=4, seat_pitch=2.00,
                        pax_per_lavatory=10),
            SeatingZone("business", n_seats=42, seats_abreast=7, seat_pitch=1.52,
                        pax_per_lavatory=20),
            SeatingZone("economy", n_seats=328, seats_abreast=10, seat_pitch=0.81),
        ],
        cabin_height=2.30,
        floor_thickness=0.25,
    )
    return [main]
