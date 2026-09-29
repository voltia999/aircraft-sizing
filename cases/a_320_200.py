"""Airbus A320-200 (ceo): the 150-seat case of the guion V4.

Mission, aerodynamics and design choices follow
Dimensionamiento_preliminar_aeronave_Raymer_V4.pdf (Raymer 7th edition).
Reference figures are the ones the guion compares against (Table 7 and notes).
"""

from math import radians

from constants import NM, KT, HOUR
from data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone


def case() -> tuple:
    mission = Mission(
        n_pax=150,                    # 12 business + 138 economy
        m_pax=100.0,
        n_trip=6,                     # 2 pilots + 4 cabin crew (ORO.CC.100)
        m_trip=95.0,
        range=3000 * NM,
        mach=0.78,
        altitude=11_000,              # FL360, tropopause
        loiter=45 * 60,
        v_aprox=135 * KT,             # approach category C
        descent=False,                # guion Table 2: single 0.995 descent + landing
    )

    aero = Aerodynamics(
        AR=9.5,
        swet_sref=6.0,                # Raymer Fig. 3.6
        k_ld=15.5,                    # Raymer 3.4.4, civil jet
        taper_ratio=0.24,
        sweep_c4=radians(25.0),       # Lambda_LE ~ 28 deg -> straight-wing Oswald
        c_cruise=0.5 / HOUR,          # Raymer Table 3.3
        c_loiter=0.4 / HOUR,
        cfe=0.0026,                   # Raymer Table 12.3
        oswald_method="raymer"
    )

    design = Design(
        wing_loading=600.0,           # guion 8.3, below the ~655 landing limit
        cruise_wing_loading=550.0,    # guion 8.8, assumed for the cruise polar
        thrust_to_weight=0.30,        # guion 8.6, OEI climb above statistical 0.277
        n_engines=2,
        max_mach=0.82,
        cl_max_landing=2.8,
        mlw_fraction=0.85,
        raymer_edition=7,
        max_span=36.0,                # ICAO code C box
        decks=_decks(),
        fuselage={"diameter": 3.95, "nose": 4.0, "tailcone": 5.0},
        tail_arm_fraction=0.50,       # guion 10.1: L_HT = L_VT ~ 0.5 Lf
    )

    reference = Reference(
        name="A320-200 (ceo)",
        mtow=78_000,
        fuel_capacity=18_700,
        thrust=2 * 120e3,             # CFM56-5B4, 27 000 lbf
        wing_area=122.4, wingspan=33.9,
        aspect_ratio=9.4,
        fuselage_length=37.6,
        fuselage_width=3.95,
        s_ht=31.0, s_vt=21.5,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Guion section 9: 2-2 business, 3-3 economy, one aisle."""
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
