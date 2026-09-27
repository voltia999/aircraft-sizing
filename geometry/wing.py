import numpy as np

def wing_geometry(w0, aero, design, max_span=None) -> dict:
    s = w0 / design.wing_loading
    b = np.sqrt(aero.AR * s)
    AR = b ** 2 / s
    c_root = 2 * s / (b * (1 + aero.taper_ratio))

    return{
                "S": s, "b": b, "AR": AR,
                "c_root": c_root, "c_tip": aero.taper_ratio * c_root,
                "MAC": 2 / 3 * c_root * (1 + aero.taper_ratio + aero.taper_ratio ** 2) /
                  (1 + aero.taper_ratio)
            }