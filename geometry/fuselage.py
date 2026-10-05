from dataclasses import dataclass
from math import ceil
import numpy as np


# Cabin standards: defaults of the Deck fields, override them per deck
AISLE_WIDTH = 0.51          # m, per aisle
CLEARANCE_PER_SEAT = 0.05   # m, armrests and side clearance
LD3_HEIGHT = 1.63           # m, IATA standard container
LD3_45_HEIGHT = 1.14        # m, narrow-body container
LAVATORY_LENGTH = 0.95      # m, length of one lavatory
GALLEY_MODULE = 0.90        # m, length of one galley unit
EXIT_PAIR_LENGTH = 1.10     # m, vestibule at each pair of doors
STAIRCASE_LENGTH = 1.50     # m, per staircase
PAX_PER_TYPE_A_PAIR = 110   # CS 25.807, type A exits


@dataclass
class SeatingZone():
    name: str
    seats_abreast: int
    n_seats: int
    seat_width: float = 0.46
    seat_pitch: float = 0.81
    aisles: int = 2
    pax_per_lavatory: int = None   # None -> deck value


    @property
    def n_rows(self) -> int:
        return ceil(self.n_seats / self.seats_abreast)

    @property
    def length(self) -> float:
        return self.n_rows * self.seat_pitch


@dataclass
class Deck:
    """A passenger deck: seating zones plus services."""
    name: str
    zones: list
    aisles: int = 2
    n_staircases: int = 0
    pax_per_galley_module: int = 100
    pax_per_lavatory: int = 50
    cabin_height: float = 2.30
    floor_thickness: float = 0.25
    aisle_width: float = AISLE_WIDTH
    clearance_per_seat: float = CLEARANCE_PER_SEAT
    lavatory_length: float = LAVATORY_LENGTH
    galley_length: float = GALLEY_MODULE
    exit_pair_length: float = EXIT_PAIR_LENGTH
    pax_per_exit_pair: int = PAX_PER_TYPE_A_PAIR
    staircase_length: float = STAIRCASE_LENGTH
 
    @property
    def n_seats(self) -> int:
        return sum(z.n_seats for z in self.zones)
 
    @property
    def seats_abreast(self) -> int:
        """Widest zone drives the cabin width."""
        return max(z.seats_abreast for z in self.zones)
 
    @property
    def seat_width(self) -> float:
        return max(z.seat_width for z in self.zones)


# --- cross-section --------------------------------------------------------
def cabin_width(deck: Deck) -> float:
    """Inner width required by seats, aisles and clearances [m]."""
    n = deck.seats_abreast
    return n * deck.seat_width + deck.aisles * deck.aisle_width + n * deck.clearance_per_seat
 
 
def external_width(deck: Deck, structure_per_side: float = 0.10) -> float:
    """Outer width: cabin width plus structure and insulation [m]."""
    return cabin_width(deck) + 2 * structure_per_side
 
 
def hold_height(container_height: float = LD3_HEIGHT,
                clearance: float = 0.10) -> float:
    """Cargo hold height for the given container (LD3, LD3-45) [m]."""
    return container_height + clearance
 
 
def section_height(decks: list, keel: float = 0.20, crown: float = 0.35,
                   hold: float = None) -> float:
    """Total section height: keel + hold + (floor + cabin) per deck + crown [m]."""
    hold = hold_height() if hold is None else hold
    stack = keel + hold + crown
    for deck in decks:
        stack += deck.floor_thickness + deck.cabin_height
    return stack
 
 
def equivalent_diameter(width: float, height: float) -> float:
    """Raymer: non-circular sections use a diameter from the cross-section area."""
    return np.sqrt(width * height)

# --- length ---------------------------------------------------------------
def required_exit_pairs(n_seats: int, pax_per_pair: int = PAX_PER_TYPE_A_PAIR) -> int:
    """Minimum pairs of type A exits, CS 25.807."""
    return ceil(n_seats / pax_per_pair)
 
 
def deck_length(deck: Deck) -> dict:
    """Length breakdown of one deck [m]."""
    seating = sum(z.length for z in deck.zones)
    lavatories = sum(ceil(z.n_seats / (z.pax_per_lavatory or deck.pax_per_lavatory))
                     for z in deck.zones) * deck.lavatory_length
    galleys = ceil(deck.n_seats / deck.pax_per_galley_module) * deck.galley_length
    exits = required_exit_pairs(deck.n_seats, deck.pax_per_exit_pair) * deck.exit_pair_length
    stairs = deck.n_staircases * deck.staircase_length
    return {
        "seating": seating, "galleys": galleys, "lavatories": lavatories,
        "exits": exits, "stairs": stairs,
        "total": seating + galleys + lavatories + exits + stairs,
    }
 
 
def nose_length(height: float, radome_height: float = 1.00,
                upper_angle: float = 20.0, lower_angle: float = 15.0) -> float:
    """Nose length from the contour criterion (Raymer, Fig. 8.2).
 
    A favourable pressure gradient allows steeper angles at the front.
    """
    return (height - radome_height) / (np.tan(np.radians(upper_angle))
                                       + np.tan(np.radians(lower_angle)))
 
 
def tailcone_length(height: float, end_height: float = 0.80,
                    upper_angle: float = 11.0, lower_angle: float = 15.0) -> float:
    """Tailcone length from the contour criterion (Raymer, Fig. 8.2).
 
    Deviation from the freestream must stay below 10-12 deg, up to 15 deg
    on the underside, to keep the flow attached.
    """
    return (height - end_height) / (np.tan(np.radians(upper_angle))
                                    + np.tan(np.radians(lower_angle)))
 
 
def fineness_ratio(length: float, diameter: float) -> float:
    """Raymer: optimum is 6-8 for subsonic aircraft at constant volume."""
    return length / diameter
 
 
# Raymer Table 6.3, jet transport (metric), by edition: Lf = a * W0^C1
TABLE_6_3 = {6: {"a": 0.287, "C1": 0.43},
             7: {"a": 0.690, "C1": 0.360}}

def statistical_length(w0: float, edition: int = 7) -> float:
    """Raymer, Table 6.3, jet transport (metric)."""
    t = TABLE_6_3[edition]
    return t["a"] * w0 ** t["C1"]

# --- assembly -------------------------------------------------------------
# fuselage_geometry option -> parameter of nose_length / tailcone_length
NOSE_OPTIONS = {"radome_height": "radome_height",
                "nose_upper_angle": "upper_angle", "nose_lower_angle": "lower_angle"}
TAILCONE_OPTIONS = {"tailcone_end_height": "end_height",
                    "tailcone_upper_angle": "upper_angle", "tailcone_lower_angle": "lower_angle"}
FUSELAGE_OPTIONS = ({"diameter", "nose", "tailcone", "structure_per_side", "keel",
                     "crown", "hold", "edition"} | set(NOSE_OPTIONS) | set(TAILCONE_OPTIONS))

def _pick(kwargs: dict, options: dict) -> dict:
    """The kwargs present in options, renamed to the function's parameters."""
    return {param: kwargs[key] for key, param in options.items() if key in kwargs}

def fuselage_geometry(decks: list, w0: float = None, **kwargs) -> dict:
    """Full fuselage sizing from the cabin layout.
 
    The length is driven by the longest deck; w0 is optional and used
    only for the statistical check.

    Optional kwargs fix project decisions instead of computing them:
    'diameter' (circular section), 'nose' and 'tailcone' lengths [m].
    Other kwargs tune the computed section ('structure_per_side', 'keel',
    'crown', 'hold') and contours ('radome_height', 'nose_upper_angle',
    'nose_lower_angle', 'tailcone_end_height', 'tailcone_upper_angle',
    'tailcone_lower_angle'; angles in degrees).
    """
    unknown = set(kwargs) - FUSELAGE_OPTIONS
    if unknown:
        raise TypeError(f"Unknown fuselage options {sorted(unknown)}; "
                        f"valid: {sorted(FUSELAGE_OPTIONS)}")
    main = max(decks, key=lambda d: deck_length(d)["total"])
    if kwargs.get("diameter"):
        width = height = d_eq = kwargs["diameter"]
    else:
        width = external_width(main, kwargs.get("structure_per_side", 0.10))
        height = section_height(decks, kwargs.get("keel", 0.20),
                                kwargs.get("crown", 0.35), kwargs.get("hold"))
        d_eq = equivalent_diameter(width, height)
    cabin = deck_length(main)["total"]
    nose = kwargs.get("nose") or nose_length(height, **_pick(kwargs, NOSE_OPTIONS))
    tail = kwargs.get("tailcone") or tailcone_length(height, **_pick(kwargs, TAILCONE_OPTIONS))
    length = cabin + nose + tail
    result = {
        "cabin_widths": {d.name: cabin_width(d) for d in decks},
        "external_width": width, "section_height": height,
        "equivalent_diameter": d_eq,
        "deck_lengths": {d.name: deck_length(d) for d in decks},
        "cabin_length": cabin, "nose": nose, "tailcone": tail,
        "length": length, "fineness": fineness_ratio(length, d_eq),
    }
    if w0:
        result["statistical_length"] = statistical_length(w0, kwargs.get("edition", 7))
    return result

