
from math import radians

from constants import NM, KT, HOUR
from data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone

def case() -> tuple:
    mission = Mission(
        n_pax=240,                    # 20 business + 200 economy (2-class)
        n_trip=10,                     # 2 pilots + 6 cabin crew (H)
        range=6800e3,              # (H) range with 2-class payload
        mach=0.80,
        altitude=12_000,              # FL350
        loiter=45 * 60,
        v_aprox=135 * KT,             # (H)
    )

    aero = Aerodynamics(
        AR=8.80,                      # 43.90^2 / 219
        swet_sref=6.0,                # (H) Raymer Fig. 3.6
        taper_ratio=0.28,             # (H)
        sweep_c4=radians(28.0),
        c_cruise=0.5 / HOUR,          # Raymer Table 3.3, high-bypass turbofan
        c_loiter=0.4 / HOUR,
    )

    design = Design(
        wing_loading=740.0,           # (H) close to the real 749 kg/m2
        thrust_to_weight=0.30,        # (H) real 2 x 238 kN / MTOW = 0.296
        n_engines=2,
        max_mach=0.84,
        cl_max_landing=2.6,           # (H) Fowler flaps + slats
        mlw_fraction=0.76,            # (H) 124 000 / 164 000
        max_span=52.0,                # ICAO code D box
        decks=_decks(),
    )

    reference = Reference(
        name="A310-300",
        mtow=141_900, oew=80_000,
        wing_area=219.0, wingspan=43.90,
        fuselage_length=46.66,
        thrust=2 * 238e3,             # CF6-80C2A2, 53 500 lbf
        aspect_ratio=8.80,
        fuselage_width=5.64,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Single deck, two classes, twin aisle, 8 abreast in economy (2-4-2)."""
    main = Deck(
        name="main",
        zones=[
            SeatingZone("business", n_seats=24, seats_abreast=6, seat_pitch=0.97,
                        pax_per_lavatory=20, aisles=2), 
            SeatingZone("economy", n_seats=216, seats_abreast=8, seat_pitch=0.81, aisles=2),
        ],
        cabin_height=2.30,
        floor_thickness=0.25,
    )
    return [main]
