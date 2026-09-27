"""Boeing 737-800 (high gross weight): mission requirements and assumptions.

Reference figures: Boeing 737 Airplane Characteristics for Airport Planning
and the EASA/FAA type certificate data sheets.
"""

from math import radians

from constants import NM, KT
from data import Mission, Aerodynamics, Design, Reference
from geometry.fuselage import Deck, SeatingZone


def case() -> tuple:
    mission = Mission(
        n_pax=162,                    # 12 business + 150 economy (Boeing 2-class)
        n_trip=6,                     # 2 pilots + 4 cabin crew (ORO.CC.100: min 4)
        m_trip=95.0,
        range=2900 * NM,       # slightly below the ~2935 NM reference
        mach=0.785,
        altitude=11_000,              # FL360, tropopause
        loiter=45 * 60,
        v_aprox=145 * KT,      # (H) faster than the A320, near cat C/D
    )

    aero = Aerodynamics(
        AR=9.42,            # 34.32^2 / 125, span without winglets
        swet_sref=6.0,                # (H) typical narrow-body value
        taper_ratio=0.24,             # (H)
        sweep_c4=radians(25.0),
        c_cruise=0.5 / 3600,
        c_loiter=0.4 / 3600,
    )

    design = Design(
        wing_loading=620.0,           # (H) close to the real 634 kg/m2
        thrust_to_weight=0.31,        # twin: OEI climb drives it above the
        n_engines=2,                  #       statistical 0.25
        max_mach=0.82,
        cl_max_landing=2.6,           # Fig. 5.3, double-slotted flap + slat at 25 deg
        mlw_fraction=0.83,            # 65315 / 79015
        vref_factor=1.23,             # CS-25
        max_span=36.0,                # ICAO code C box
        raymer_edition=6,             # guion v2, 8.6: Table 6.1 with a = 0.32, b = 0.66
        decks=_decks(),
        # Guion v2, 9.1-9.2: D fixed for LD3-45 containers, nose and tailcone assumed
        fuselage={"diameter": 3.95, "nose": 4.0, "tailcone": 5.0},
        tail_arm_fraction=0.40,       # guion v2, 10.1: L_HT = L_VT ~ 0.40 Lf
    )

    # Weights, fuel, cabin section: Boeing D6-58325-7 Rev C (2025), 2.1.3 and 2.5.2.
    # Wing and tail geometry, fuselage length/height: b737.org.uk detailed tech data.
    reference = Reference(
        name="737-800 (HGW)",
        mtow=79_015, oew=41_412,
        mlw=66_360, mzfw=62_731,
        max_payload=21_318,
        fuel_capacity=20_897,           # 26 024 L usable
        thrust=2 * 117e3,               # CFM56-7B26, 26 300 lbf
        wing_area=124.58, wingspan=34.32,   # span without winglets
        aspect_ratio=9.45, taper_ratio=0.159, sweep_c4=25.02,
        root_chord=7.88, tip_chord=1.25, mac=3.96,
        fuselage_length=38.08,          # fuselage only; overall length 39.47 m
        fuselage_width=3.76, fuselage_height=4.01,
        cabin_width=3.54,
        s_ht=32.78, s_vt=26.44,
        s_elevator=6.55, s_rudder=5.22,
    )

    return mission, aero, design, reference


def _decks() -> list:
    """Single deck, two classes, one aisle, 6 abreast in economy."""
    main = Deck(
        name="main",
        zones=[
            SeatingZone("business", n_seats=12, seats_abreast=4, seat_pitch=0.97, seat_width=0.46,
                        pax_per_lavatory=20),
            SeatingZone("economy", n_seats=150, seats_abreast=6, seat_pitch=0.81, seat_width=0.46,
                        pax_per_lavatory=50),
        ],
        aisles=1,
        cabin_height=2.20,
        floor_thickness=0.20,
        pax_per_galley_module=100,
    )
    return [main]