import argparse

import weight, constraints
from geometry import wing, fuselage, tail
from cases import a_300b4, a_310_300, a_350_900, a_380, b_707_320b, b_727_200, b_737_800, b_747_400
from constants import G
from geometry.tail import implied_coefficients

CASES = {
    "707-320b": b_707_320b.case, "727-200": b_727_200.case,
    "737-800": b_737_800.case, "747-400": b_747_400.case,
    "a300b4": a_300b4.case, "a310-300": a_310_300.case,
    "a350-900": a_350_900.case, "a380": a_380.case,
}

def run(case_name: str, refined: bool = True, edition: int = None) -> dict:
    mission, aero, design, reference = CASES[case_name]()
    if edition:
        design.raymer_edition = edition

    result = weight.resolve(mission, aero, design, refined=refined)
    limits = {
        "landing": constraints.landing_wing_loading(mission, design),
        "cruise": constraints.cruise_wing_loading(mission, aero),
    }

    w = wing.wing_geometry(result.w0, aero, design, max_span=design.max_span)
    f = fuselage.fuselage_geometry(design.decks, w0=result.w0,
                                  edition=design.raymer_edition, **design.fuselage)
    t = tail.tail_geometry(w, f["length"],
                           tail.TailCoefficients(arm_fraction=design.tail_arm_fraction))
    return {"weights": result, "limits": limits, "design": design,
            "wing": w, "fuselage": f, "tail": t, "reference": reference}

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
    parser.add_argument("case", choices=CASES, default="a380", nargs="?")
    parser.add_argument("--first-order", action="store_true")
    parser.add_argument("--edition", type=int, choices=(6, 7),
                        help="Raymer edition for the statistical tables (default: case value)")
    args = parser.parse_args()
    report(run(args.case, refined=not args.first_order, edition=args.edition))