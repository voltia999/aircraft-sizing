# methods — Aerodinámica, pesos y restricciones

Los métodos de Raymer que llevan de la misión al MTOW (W0) y a los límites de
carga alar. Leen las dataclasses de [`core/`](../core/README.md); la geometría
que sale de W0 está en [`geometry/`](../geometry/README.md).

| Archivo | Contenido | Raymer |
|---|---|---|
| `aerodynamic.py` | Atmósfera, L/D, flecha, Oswald, polar (CD0, K) | 3.4, 6.3.7, 12.5–12.6 |
| `weight.py` | Fracciones de misión, fracción en vacío e iteración de W0 | cap. 3 y 6.3 |
| `constraints.py` | Límites de carga alar y T/W estadístico | cap. 5 |

`weight` usa `aerodynamic`, y `constraints` usa `aerodynamic`; ninguno depende
de `geometry`.

---

## `aerodynamic.py`

| Función | Fórmula |
|---|---|
| `cruise_density`, `velocity_rel` | ISA (`ambiance`) a `altitude`; V = M·a |
| `ld_max` | `aero.ld_max` si está fijado; si no, K_LD · √(AR / (Swet/Sref)) |
| `ld_max_polar` | (L/D)max de la polar, 1 / (2·√(CD0·K)); espera del refinado |
| `ld_cruise` | 0.866 · (L/D)max (jet) |
| `ld_cruise_refined` | 1 / (q·CD0/(W/S) + (W/S)·K/q), con q = ½ρV²; W/S en N/m² (el argumento `wing_loading`, o `cruise_wing_loading`, o `wing_loading` de diseño) |
| `sweep_le` | atan(tan Λc/4 + (1−λ) / (AR(1+λ))) |
| `oswald` | `Aerodynamics.oswald` si está fijado; si no, e₀ = 1 − 0.045·AR^0.68 y, si Λ_LE > 30°: 4.61·e₀·cos(Λ_LE)^0.15 − 3.1, si no: 1.78·e₀ − 0.64 (ecs. 12.48–12.49) |
| `oswald_in_typical_range` | e dentro de 0.70–0.85 (Raymer 12.6.1); el informe avisa si no |
| `cd0` | Cfe · Swet/Sref |
| `k` | 1 / (π·AR·e) |

---

## `weight.py`

- **Peso fijo**: `w_fixed = n_pax·m_pax + n_trip·m_trip`.
- **Crucero** (Breguet, ec. 6.11): `F_cruise = exp(−R·c / (V·(L/D)crucero))`.
  Con `design` (cálculo refinado) usa `ld_cruise_refined` con la W/S real a
  mitad de crucero; si no, `ld_cruise`.
- **W/S a mitad de crucero** (`mid_cruise_wing_loading`, nota a la ec. 6.13):
  `(W/S)_mid = (W0/S)·F_despegue·F_ascenso·(1 + F_crucero)/2`, iterada porque
  `F_crucero` depende de la L/D. Si `Design.cruise_wing_loading` está fijado,
  se usa ese valor.
- **Espera** (Breguet, ec. 6.14): `F_loiter = exp(−E·c / (L/D)max)`, con la
  (L/D)max de `ld_max` en primer orden y la de la polar (`ld_max_polar`) en el refinado.
- **Subida refinada** (6.3.6): `F_ascent_refined = 1.0065 − 0.0325·M`.
- **Combustible**: `Wf/W0 = F_reserve · (1 − ∏ fracciones)`; `F_descent` solo
  entra si `mission.descent` es `True`.
- **Fracción en vacío**:
  - Primer orden, `F_empty` (Tabla 3.1): `We/W0 = a·W0^C·Kvs·Kc`.
  - Refinado, `F_empty_refined` (Tabla 6.1):
    - 6.ª ed.: `We/W0 = (a + b·W0^C1·AR^C2·(T/W)^C3·(W0/S)^C4·Mmax^C5)·Kvs·Kc`
    - 7.ª ed.: `We/W0 = a·W0^C1·AR^C2·(T/W)^C3·(W0/S)^C4·Mmax^C5·Kvs·Kc`
  - La Tabla 6.1 viene en unidades imperiales en **las dos ediciones** (W0 en
    lb, W0/S en lb/ft²). `TABLE_6_1` convierte a kg y kg/m² la constante que
    multiplica a W0^C1·(W0/S)^C4: `b` en la 6.ª (0.66 → 0.645) y `a` en la 7.ª
    (0.869 → 1.089).
  - `Kc = Design.k_composite`: 0.95 para estructura de compuesto (Raymer cap. 3).

### `resolve(mission, aero, design=None, refined=False, w0_initial=5e5, tol=1e-2, max_iter=1000)`

Itera por punto fijo

```
W0 = (Wcrew + Wpayload) / (1 − Wf/W0 − We/W0)
```

hasta que |ΔW0| < `tol` (kg) y devuelve un `Result` (ver `core/`).

- `refined=True` usa la subida dependiente de Mach, la L/D de crucero de la
  polar y la Tabla 6.1, y exige un `Design`.
- Lanza `ValueError` si `Wf/W0 + We/W0 ≥ 1` (misión no cerrable) y
  `RuntimeError` si no converge.

```python
from methods import weight
result = weight.resolve(mission, aero, design, refined=True)
result.w0, result.w_empty, result.w_fuel
```

---

## `constraints.py`

- `landing_wing_loading`: Vstall = V_aprox / vref_factor;
  W/S_aterrizaje = ½·ρ₀·Vstall²·CLmax / g, referida a despegue dividiendo por `mlw_fraction`.
- `cruise_wing_loading`: W/S para el CL óptimo de crucero, CL_opt = √(CD0 / 3K),
  referida a despegue dividiendo por las fracciones de despegue y subida.
- `statistical_thrust_to_weight`: T/W = a·Mmax^C (Tabla 5.3, `TABLE_5_3`):
  6.ª ed. a = 0.267, C = 0.363; 7.ª ed. a = 0.297, C = 0.350.

Los límites se muestran en el informe, pero no modifican el diseño: W/S y T/W
son entradas de `Design`.
