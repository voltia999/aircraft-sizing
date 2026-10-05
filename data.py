from dataclasses import dataclass, field
import numpy as np

from constants import NM, KT, HOUR, G


@dataclass
class Mission():
    n_pax: int
    m_pax: float = 100.0          # kg por pasajero con equipaje
    n_trip: int = 6
    m_trip: float = 95.0   # kg por tripulante
    range: float = 3000 * NM    # m
    mach: float = 0.78
    altitude: float = 11000.0      # m
    loiter: float = 20 * 60       # s
    v_aprox: float = 135 * KT  # m/s
    # Short segment fractions, Raymer Table 3.2
    F_takeoff: float = 0.970
    F_ascent: float = 0.985
    F_descent: float = 0.990
    descent: bool = True          # False: Raymer 6th, descent included in cruise
    F_landing: float = 0.995
    F_reserve: float = 1.06       # 6 % trapped and reserve fuel


@dataclass
class  Aerodynamics():

    AR: float = 9.5
    swet_sref:float = 6.0
    k_ld: float = 15.5
    ld_max: float = None           # fixed (L/D)max; None -> K_LD * sqrt(AR / Swet/Sref)
    taper_ratio: float = 0.24
    sweep_c4: float = np.radians(25)
    c_cruise: float = 0.5 / HOUR   # 1/s (TSFC 0.5 1/h)
    c_loiter: float = 0.5 / HOUR   # 1/s
    cfe: float = 0.0026

@dataclass
class Design:
    """Project decisions (initial sizing)."""
    wing_loading: float = 600.0        # kg/m2
    cruise_wing_loading: float = None  # kg/m2, W/S for the cruise polar; None -> wing_loading
    thrust_to_weight: float = 0.30
    n_engines: int = 2
    max_mach: float = 0.82
    cl_max_landing: float = 2.8
    mlw_fraction: float = 0.85         # MLW / MTOW
    vref_factor: float = 1.23          # CS-25
    k_vs: float = 1.0                  # 1.04 for variable sweep
    table_6_1_metric: bool = True
    raymer_edition: int = 7            # 6 or 7: statistical tables 3.1, 6.1, 6.3
    max_span: float = None             # m, airport box limit
    decks: list = field(default_factory=list)
    fuselage: dict = field(default_factory=dict)   # fixed choices: diameter, nose, tailcone [m]
    tail_arm_fraction: float = 0.50    # tail arm / fuselage length
    tail_arm_length: str = "cabin"     # Lf for the tail arm: "cabin" layout or "statistical" (Table 6.3)


@dataclass
class Reference:
    """Actual aircraft used for comparison (validation only)."""
    name: str
    mtow: float
    oew: float = 0.0
    wing_area: float = 0.0
    wingspan: float = 0.0
    fuselage_length: float = 0.0
    mlw: float = 0.0                   # kg
    mzfw: float = 0.0                  # kg
    max_payload: float = 0.0           # kg, MZFW - OEW
    fuel_capacity: float = 0.0         # kg
    thrust: float = 0.0                # N, all engines
    aspect_ratio: float = 0.0
    taper_ratio: float = 0.0
    sweep_c4: float = 0.0              # deg
    root_chord: float = 0.0            # m
    tip_chord: float = 0.0             # m
    mac: float = 0.0                   # m
    fuselage_width: float = 0.0        # m
    fuselage_height: float = 0.0       # m
    cabin_width: float = 0.0           # m, interior trim to trim
    cabin_length: float = 0.0          # m, longest deck
    s_ht: float = 0.0                  # m2
    s_vt: float = 0.0                  # m2
    s_elevator: float = 0.0            # m2
    s_rudder: float = 0.0              # m2

    @property
    def wing_loading(self) -> float:
        return self.mtow / self.wing_area if self.wing_area else 0.0

    @property
    def thrust_to_weight(self) -> float:
        return self.thrust / (self.mtow * G) if self.thrust else 0.0
