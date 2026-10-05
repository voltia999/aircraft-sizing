import argparse
import importlib.util
from pathlib import Path

from methods import weight, constraints, aerodynamic
from geometry import wing, fuselage, tail
from core.constants import G
from geometry.tail import implied_coefficients

ROOT = Path(__file__).resolve().parent
# example/ is versioned; cases/ holds local working cases and may not exist.
CASE_FOLDERS = ("example", "cases")

def load_cases() -> dict:
    """{name: case function} of every module with a case() in CASE_FOLDERS.

    The name is the module's NAME, or its file name with '-' for '_'.
    """
    cases = {}
    for folder in CASE_FOLDERS:
        for path in sorted((ROOT / folder).glob("*.py")):
            spec = importlib.util.spec_from_file_location(f"{folder}.{path.stem}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "case"):
                continue
            name = getattr(module, "NAME", path.stem.replace("_", "-"))
            if name in cases:
                raise ValueError(f"Duplicate case name '{name}' in {path}")
            cases[name] = module.case
    return cases

CASES = load_cases()

def run(case_name: str, refined: bool = True, edition: int = None,
        descent: bool = None) -> dict:
    mission, aero, design, reference = CASES[case_name]()
    if edition:
        design.raymer_edition = edition
    if descent is not None:
        mission.descent = descent

    result = weight.resolve(mission, aero, design, refined=refined)
    limits = {
        "landing": constraints.landing_wing_loading(mission, design),
        "cruise": constraints.cruise_wing_loading(mission, aero),
    }
    aero_summary = aerodynamics_summary(mission, aero, design, refined)

    w = wing.wing_geometry(result.w0, aero, design, max_span=design.max_span)
    f = fuselage.fuselage_geometry(design.decks, w0=result.w0,
                                  edition=design.raymer_edition, **design.fuselage)
    arm_length = f["statistical_length"] if design.tail_arm_length == "statistical" else f["length"]
    t = tail.tail_geometry(w, arm_length, design.tail, design.controls)
    return {"weights": result, "limits": limits, "aero": aero_summary,
            "design": design,
            "wing": w, "fuselage": f, "tail": t, "reference": reference}

def aerodynamics_summary(mission, aero, design, refined: bool) -> dict:
    """Polar and the cruise and loiter L/D used by the sizing."""
    if refined:
        start = mission.F_takeoff * weight.F_ascent_refined(mission)
        ws = weight.mid_cruise_wing_loading(mission, aero, design, start)
        ld_cruise = aerodynamic.ld_cruise_refined(aero, mission, design, ws)
        ld_loiter = aerodynamic.ld_max_polar(aero)
    else:
        ld_cruise, ld_loiter = aerodynamic.ld_cruise(aero), aerodynamic.ld_max(aero)
    return {"e": aerodynamic.oswald(aero), "e_ok": aerodynamic.oswald_in_typical_range(aero),
            "cd0": aerodynamic.cd0(aero), "k": aerodynamic.k(aero),
            "ld_cruise": ld_cruise, "ld_loiter": ld_loiter}

def report(out: dict) -> None:
    """Prints the summary table of section 11."""
    r, ref = out["weights"], out["reference"]
    w, f, t, d = out["wing"], out["fuselage"], out["tail"], out["design"]

    def row(label, value, unit="", real=None, fmt=",.1f"):
        line = f"  {label:<24}{value:>12{fmt}} {unit:<6}"
        if real:
            line += f"{real:>12{fmt}}  {100 * (value / real - 1):+6.1f} %"
        print(line)

    def header(title):
        print(f"\n{title}")
        print("-" * 70)

    print(f"Case: {r.case}   Raymer edition: {d.raymer_edition}   Reference: {ref.name}")
    print(f"  {'':<24}{'computed':>12} {'':<6}{'actual':>12}  {'error':>8}")

    header("Weights")
    row("MTOW", r.w0, "kg", ref.mtow, ",.0f")
    row("OEW", r.w_empty, "kg", ref.oew, ",.0f")
    row("MLW", d.mlw_fraction * r.w0, "kg", ref.mlw, ",.0f")
    row("Fuel (vs capacity)", r.w_fuel, "kg", ref.fuel_capacity, ",.0f")
    row("We/W0", r.we_w0, fmt=".3f")
    row("Wf/W0", r.wf_w0, fmt=".3f")
    row("Iterations", len(r.history), fmt="d")

    a = out["aero"]
    header("Aerodynamics")
    row("Oswald e", a["e"], fmt=".3f")
    if not a["e_ok"]:
        low, high = aerodynamic.OSWALD_TYPICAL_RANGE
        print(f"  ! e outside Raymer's typical {low}-{high} (sec. 12.6.1)")
    row("CD0", a["cd0"], fmt=".4f")
    row("K", a["k"], fmt=".4f")
    row("L/D cruise", a["ld_cruise"], fmt=".2f")
    row("L/D loiter", a["ld_loiter"], fmt=".2f")

    header("Wing and thrust loading")
    row("W0/S", r.w0 / w["S"], "kg/m2", ref.wing_loading)
    row("T/W", d.thrust_to_weight, fmt=".3f", real=ref.thrust_to_weight)
    row("Total thrust", d.thrust_to_weight * r.w0 * G / 1e3, "kN", ref.thrust / 1e3, ",.0f")
    for name, value in out["limits"].items():
        row(f"Max W/S {name}", value, "kg/m2")

    header("Wing")
    row("Area S", w["S"], "m2", ref.wing_area)
    row("Span b", w["b"], "m", ref.wingspan, ".2f")
    row("Aspect ratio AR", w["AR"], fmt=".2f", real=ref.aspect_ratio)
    row("Root chord", w["c_root"], "m", fmt=".2f")
    row("Tip chord", w["c_tip"], "m", fmt=".2f")
    row("MAC", w["MAC"], "m", fmt=".2f")

    header("Fuselage")
    row("Length", f["length"], "m", ref.fuselage_length, ".2f")
    row("Statistical length", f.get("statistical_length", 0), "m", fmt=".2f")
    row("Cabin length", f["cabin_length"], "m", ref.cabin_length, ".2f")
    row("Nose", f["nose"], "m", fmt=".2f")
    row("Tailcone", f["tailcone"], "m", fmt=".2f")
    row("External width", f["external_width"], "m", ref.fuselage_width, ".2f")
    row("Section height", f["section_height"], "m", ref.fuselage_height, ".2f")
    row("Equivalent diameter", f["equivalent_diameter"], "m", fmt=".2f")
    row("Fineness ratio", f["fineness"], fmt=".2f")

    header("Tail")
    row("Tail arm", t["arm"], "m", fmt=".2f")
    row("Horizontal S", t["s_ht"], "m2", ref.s_ht)
    row("Vertical S", t["s_vt"], "m2", ref.s_vt)
    if ref.s_ht and ref.s_vt:
        # Actual tail areas on the computed wing and arm
        c = implied_coefficients(ref.s_ht, ref.s_vt, w["MAC"], w["b"], w["S"], t["arm"])
        row("Implied c_HT (actual)", c["c_ht"], fmt=".2f")
        row("Implied c_VT (actual)", c["c_vt"], fmt=".3f")
    for name, value in t["controls"].items():
        row(name.capitalize(), value, "m2")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=CASES, default="guion-v4", nargs="?")
    parser.add_argument("--first-order", action="store_true")
    parser.add_argument("--edition", type=int, choices=(6, 7),
                        help="Raymer edition for the statistical tables (default: case value)")
    parser.add_argument("--descent", action=argparse.BooleanOptionalAction,
                        help="include the descent segment (default: case value)")
    args = parser.parse_args()
    report(run(args.case, refined=not args.first_order, edition=args.edition,
               descent=args.descent))