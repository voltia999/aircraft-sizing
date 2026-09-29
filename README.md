# sizing — Dimensionamiento preliminar de aviones de transporte a reacción

Herramienta en Python para el dimensionamiento conceptual de un avión de
transporte siguiendo *Raymer, Aircraft Design: A Conceptual Approach*
(tablas estadísticas de la 6.ª y 7.ª edición). A partir de la misión y de unas
hipótesis aerodinámicas y de diseño calcula:

1. **Pesos**: MTOW (W0), peso en vacío y combustible, por iteración.
2. **Restricciones de carga alar**: W/S máximo por aterrizaje y por crucero.
3. **Ala**: superficie, envergadura, cuerdas y MAC.
4. **Fuselaje**: sección y longitud a partir de la distribución de cabina.
5. **Empenaje**: superficies de cola por coeficientes de volumen y superficies de mando.

Cada resultado se compara con los datos reales de un avión de referencia
(A300, A310, A350, A380, 707, 727, 737, 747).

Todas las magnitudes están en SI; las **masas se expresan en kg** y la carga
alar en **kg/m²**.

---

## Instalación

Requiere Python 3.10+ y:

```bash
pip install numpy ambiance pytest
```

`ambiance` proporciona la atmósfera ISA (densidad y velocidad del sonido en crucero).

## Uso

Los módulos se importan como módulos de primer nivel, así que hay que ejecutar
desde este directorio:

```bash
python main.py                    # caso por defecto: a380, cálculo refinado
python main.py 737-800            # otro caso
python main.py 737-800 --first-order   # método de primer orden (Tabla 3.1)
python main.py a350-900 --edition 6    # fuerza la edición de Raymer (6 o 7)
python main.py a380-v2 --no-descent    # sin segmento de descenso (--descent lo fuerza)
```

Casos disponibles: `707-320b`, `727-200`, `737-800`, `747-400`, `a300b4`,
`a310-200`, `a310-300`, `a350-900`, `a380`, `a380-v2`.

Salida (extracto de `python main.py 737-800`):

```
Case: refined   Raymer edition: 6   Reference: 737-800 (HGW)
                              computed             actual     error

Weights
----------------------------------------------------------------------
  MTOW                          74,070 kg          79,015    -6.3 %
  OEW                           38,627 kg          41,412    -6.7 %
  ...
Wing
----------------------------------------------------------------------
  Area S                         119.5 m2           124.6    -4.1 %
  Span b                         33.55 m            34.32    -2.3 %
  ...
```

La columna *error* es `calculado / real − 1`; solo aparece cuando el caso
define el dato real correspondiente.

Uso desde Python:

```python
from main import run, report

out = run("737-800", refined=True, descent=False)   # dict con weights, limits, wing, fuselage, tail...
print(out["weights"].w0)             # MTOW [kg]
report(out)
```

---

## Estructura

```
sizing/
├── main.py            CLI: ejecuta un caso completo e imprime el informe
├── constants.py       Constantes físicas y conversiones de unidades
├── data.py            Dataclasses de entrada: Mission, Aerodynamics, Design, Reference
├── results.py         Dataclass Result (salida de la iteración de pesos)
├── aerodynamic.py     Atmósfera, L/D, flecha, Oswald, polar (CD0, K)
├── weight.py          Fracciones de misión, fracción en vacío e iteración de W0
├── constraints.py     Límites de carga alar y T/W estadístico
├── geometry/
│   ├── wing.py        Geometría del ala trapezoidal
│   ├── fuselage.py    Sección y longitud del fuselaje desde la cabina
│   └── tail.py        Empenaje por coeficientes de volumen
├── cases/             Un módulo por avión de referencia
└── tests/             Regresión contra el guion (PDF Raymer V2)
```

Flujo de cálculo en `main.run()`:

```
case() ─► Mission, Aerodynamics, Design, Reference
            │
            ├─► weight.resolve() ────────► W0, We/W0, Wf/W0
            ├─► constraints.*   ─────────► W/S máx. (aterrizaje, crucero)
            ├─► wing.wing_geometry(W0) ──► S, b, cuerdas, MAC
            ├─► fuselage.fuselage_geometry(decks) ─► longitud, sección
            └─► tail.tail_geometry(ala, Lf) ─► S_HT, S_VT, mandos
```

El empenaje se calcula el último porque necesita el ala (MAC, S, b) y la
longitud del fuselaje (que fija el brazo de cola).

Detalle de las funciones geométricas, constantes y claves de retorno en
[`geometry/README.md`](geometry/README.md).

---

## Datos de entrada (`data.py`)

### `Mission` — requisitos de misión

| Campo | Defecto | Unidad | Descripción |
|---|---|---|---|
| `n_pax` | — | | Número de pasajeros (obligatorio) |
| `m_pax` | 100 | kg | Masa por pasajero con equipaje |
| `n_trip`, `m_trip` | 6, 95 | —, kg | Tripulantes y masa por tripulante |
| `range` | 3000 NM | m | Alcance de crucero |
| `mach` | 0.78 | | Mach de crucero |
| `altitude` | 11 000 | m | Altitud de crucero |
| `loiter` | 20 min | s | Tiempo de espera |
| `v_aprox` | 135 kt | m/s | Velocidad de aproximación |
| `F_takeoff`, `F_ascent`, `F_descent`, `F_landing` | 0.970, 0.985, 0.990, 0.995 | | Fracciones de segmento (Raymer Tabla 3.2; el descenso no está en la 6.ª ed.) |
| `descent` | `True` | | Incluye `F_descent`; `False` = Raymer 6.ª ed. (descenso dentro del crucero) |
| `F_reserve` | 1.06 | | Factor de combustible atrapado y de reserva (6 %) |

### `Aerodynamics` — hipótesis aerodinámicas

| Campo | Defecto | Descripción |
|---|---|---|
| `AR` | 9.5 | Alargamiento |
| `swet_sref` | 6.0 | Relación superficie mojada / de referencia |
| `k_ld` | 15.5 | Constante de (L/D)max = K_LD·√(AR / (Swet/Sref)) |
| `ld_max` | `None` | (L/D)max fijado a mano; con `None` se calcula con `k_ld` |
| `taper_ratio` | 0.24 | Estrechamiento λ |
| `sweep_c4` | 25° | Flecha en c/4 (**en radianes**) |
| `c_cruise`, `c_loiter` | 0.5 h⁻¹ | Consumo específico (en s⁻¹: `0.5 / HOUR`) |
| `cfe` | 0.0026 | Coeficiente de fricción equivalente |

### `Design` — decisiones de proyecto

| Campo | Defecto | Descripción |
|---|---|---|
| `wing_loading` | 600 kg/m² | Carga alar W0/S elegida |
| `cruise_wing_loading` | `None` | W/S forzada para la polar de crucero; con `None` se usa la W/S real a mitad de crucero |
| `thrust_to_weight` | 0.30 | T/W |
| `n_engines` | 2 | Número de motores |
| `max_mach` | 0.82 | Mach máximo |
| `cl_max_landing` | 2.8 | CLmax en aterrizaje |
| `mlw_fraction` | 0.85 | MLW / MTOW |
| `vref_factor` | 1.23 | Vref / Vstall (CS-25) |
| `k_vs` | 1.0 | Factor de flecha variable (1.04 si la hay) |
| `raymer_edition` | 7 | Edición de las tablas 3.1, 6.1 y 6.3 (6 o 7) |
| `max_span` | `None` | Límite de envergadura del aeropuerto (m) — ver *Limitaciones* |
| `decks` | `[]` | Lista de `Deck` (distribución de cabina) |
| `fuselage` | `{}` | Valores fijados: `diameter`, `nose`, `tailcone` [m] |
| `tail_arm_fraction` | 0.50 | Brazo de cola / longitud del fuselaje |

### `Reference` — avión real (solo validación)

Datos publicados (MTOW, OEW, MLW, superficie alar, envergadura, dimensiones de
fuselaje, superficies de cola, empuje…). Un campo a `0.0` significa "sin dato"
y no se compara. Las propiedades `wing_loading` y `thrust_to_weight` se derivan
de los demás campos.

---

## Métodos

### Aerodinámica (`aerodynamic.py`)

| Función | Fórmula |
|---|---|
| `cruise_density`, `velocity_rel` | ISA (`ambiance`) a `altitude`; V = M·a |
| `ld_max` | `aero.ld_max` si está fijado; si no, K_LD · √(AR / (Swet/Sref)) |
| `ld_cruise` | 0.866 · (L/D)max (jet) |
| `ld_cruise_refined` | 1 / (q·CD0/(W/S) + (W/S)·K/q), con q = ½ρV²; W/S en N/m² (el argumento `wing_loading`, o `cruise_wing_loading`, o `wing_loading` de diseño) |
| `sweep_le` | atan(tan Λc/4 + (1−λ) / (AR(1+λ))) |
| `oswald` | e₀ = 1 − 0.045·AR^0.68; si Λ_LE > 30°: 4.61·e₀·cos(Λ_LE)^0.15 − 3.1, si no: 1.78·e₀ − 0.64 |
| `cd0` | Cfe · Swet/Sref |
| `k` | 1 / (π·AR·e) |

### Pesos (`weight.py`)

- **Peso fijo**: `w_fixed = n_pax·m_pax + n_trip·m_trip`.
- **Crucero** (Breguet): `F_cruise = exp(−R·c / (V·(L/D)crucero))`; con `design`
  (cálculo refinado) usa `ld_cruise_refined` con la W/S real a mitad de crucero,
  si no `ld_cruise`.
- **W/S a mitad de crucero** (`mid_cruise_wing_loading`, Raymer nota a la ec. 6.13):
  `(W/S)_mid = (W0/S)·F_despegue·F_ascenso·(1 + F_crucero)/2`, iterada porque
  `F_crucero` depende de la L/D. Si `Design.cruise_wing_loading` está fijado, se usa ese valor.
- **Espera** (Breguet): `F_loiter = exp(−E·c / (L/D)max)`.
- **Subida refinada** (Raymer 6.3.6): `F_ascent_refined = 1.0065 − 0.0325·M`.
- **Combustible**: `Wf/W0 = F_reserve · (1 − ∏ fracciones)`; `F_descent` solo
  entra si `mission.descent` es `True`.
- **Fracción en vacío**:
  - Primer orden, `F_empty` (Tabla 3.1): `We/W0 = a·W0^C·Kvs`.
  - Refinado, `F_empty_refined` (Tabla 6.1):
    - 6.ª ed.: `We/W0 = (a + b·W0^C1·AR^C2·(T/W)^C3·(W0/S)^C4·Mmax^C5)·Kvs`
    - 7.ª ed.: `We/W0 = a·W0^C1·AR^C2·(T/W)^C3·(W0/S)^C4·Mmax^C5·Kvs`
      (la 7.ª ed. solo da coeficientes en unidades imperiales; `a` se convierte a métrico en `TABLE_6_1`).

**`resolve(mission, aero, design=None, refined=False, w0_initial=5e5, tol=1e-2, max_iter=1000)`**
itera por punto fijo

```
W0 = (Wcrew + Wpayload) / (1 − Wf/W0 − We/W0)
```

hasta que |ΔW0| < `tol` (kg). Devuelve un `Result` con `w0`, `wf_w0`, `we_w0`,
el historial de iteraciones y las propiedades `w_empty` y `w_fuel`.

- `refined=True` usa la subida dependiente de Mach, la L/D de crucero de la polar
  (`ld_cruise_refined`) y la Tabla 6.1, y exige un `Design`.
- Lanza `ValueError` si `Wf/W0 + We/W0 ≥ 1` (misión no cerrable) y
  `RuntimeError` si no converge.

### Restricciones (`constraints.py`)

- `landing_wing_loading`: Vstall = V_aprox / vref_factor;
  W/S_aterrizaje = ½·ρ₀·Vstall²·CLmax / g, referida a despegue dividiendo por `mlw_fraction`.
- `cruise_wing_loading`: W/S para el CL óptimo de crucero,
  CL_opt = √(CD0 / 3K), referida a despegue dividiendo por las fracciones de despegue y subida.
- `statistical_thrust_to_weight`: T/W = a·Mmax^C (Raymer Tabla 5.3, `TABLE_5_3`):
  6.ª ed. a = 0.267, C = 0.363; 7.ª ed. a = 0.297, C = 0.350.
- `is_feasible`: comprueba W/S ≤ límite de aterrizaje.

### Ala (`geometry/wing.py`)

`wing_geometry(w0, aero, design)` para un ala trapezoidal:
S = W0 / (W/S), b = √(AR·S), c_raíz = 2S / (b(1+λ)), c_punta = λ·c_raíz,
MAC = ⅔·c_raíz·(1+λ+λ²)/(1+λ). Devuelve un dict con `S`, `b`, `AR`,
`c_root`, `c_tip`, `MAC`.

### Fuselaje (`geometry/fuselage.py`)

La cabina se describe con `Deck` (cubierta) compuestas por `SeatingZone`
(zona de asientos: clase, asientos por fila, número de asientos, ancho y paso).

- **Sección**: ancho de cabina = n·ancho_asiento + pasillos·0.51 + n·0.05;
  ancho exterior = cabina + 2·estructura; altura = quilla + bodega (LD3/LD3-45)
  + (suelo + cabina) por cubierta + corona; diámetro equivalente √(ancho·alto).
- **Longitud de cubierta** (`deck_length`): filas·paso + galleys (1 módulo por
  `pax_per_galley_module`) + lavabos (redondeo por zona) + pares de salidas
  tipo A (CS 25.807, 110 pax por par) + escaleras.
- **Morro y cono de cola**: criterio de ángulos de contorno (Raymer Fig. 8.2).
- **Longitud estadística** (Tabla 6.3): Lf = a·W0^C1, solo como comprobación.

`fuselage_geometry(decks, w0=None, **kwargs)` toma la cubierta más larga como
dimensionante. Con `diameter`, `nose` o `tailcone` en `kwargs` (o en
`Design.fuselage`) esos valores se fijan en lugar de calcularse.

### Empenaje (`geometry/tail.py`)

- Brazo de cola: `arm_fraction · Lf` (0.50–0.55 motores en ala, 0.45–0.50 motores traseros).
- S_HT = c_HT·MAC·S / L_HT, S_VT = c_VT·b·S / L_VT, con c_HT = 1.00 y
  c_VT = 0.09 (Raymer Tabla 6.4, transporte a reacción) por defecto en `TailCoefficients`.
- Mandos: alerones 5 % de S, timón de profundidad 30 % de S_HT, timón de dirección 30 % de S_VT.
- `implied_coefficients` invierte el método: da los c_HT y c_VT reales de un
  avión existente sobre el ala y el brazo calculados (aparece en el informe).

---

## Añadir un caso

1. Crea `cases/<avion>.py` con una función `case()` que devuelva
   `(mission, aero, design, reference)`. Usa `cases/b_737_800.py` como plantilla.
2. Define la cabina con `Deck` / `SeatingZone` en `design.decks`.
3. Regístralo en el diccionario `CASES` de `main.py`.

Convención en los casos existentes: los comentarios `(H)` marcan hipótesis
propias, no datos publicados.

---

## Tests

```bash
python -m pytest tests
```

`tests/test_guion_v2.py` es una regresión contra
`Dimensionamiento_preliminar_aeronave_Raymer_V2.pdf` (narrow-body de 150
plazas, Raymer 6.ª ed.). Comprueba cada ecuación del guion con tolerancia
relativa del 1 % (el PDF redondea a unas tres cifras significativas).
`tests/conftest.py` añade el directorio raíz al `sys.path`.

`a380-v2` usa las entradas de `MTOW_A380_Raymer.pdf`. El PDF fija
(L/D)max = 19.5, que no sale de su K_LD = 15.5 con AR = 7.5 (daría 17.3); con
`ld_max=19.5` en el caso, esta orden reproduce su MTOW (≈ 539 700 kg):

```bash
python main.py a380-v2 --first-order --edition 6 --no-descent
```

Estado actual: **28 correctos, 2 fallos conocidos**:

- `test_cabin_length`: el guion usa 3 lavabos para 150 plazas (uno cada 50); el
  código redondea por zona (12/50 → 1, 138/50 → 3) y obtiene 4, así que la
  cabina sale 0.95 m más larga.
- `test_fuselage_length`: consecuencia del anterior (38.34 m frente a 37.5 m).

---

## Limitaciones

- `Design.max_span` se pasa a `wing_geometry` pero **no se aplica**: la
  envergadura no se recorta al límite de la caja del aeropuerto.
- La restricción de crucero y `statistical_thrust_to_weight` se informan, pero
  no modifican el diseño: W/S y T/W son entradas de `Design`.
- `is_feasible` y `Design.table_6_1_metric` no se usan en el flujo principal.
- Los módulos usan importaciones absolutas de primer nivel (`from data import …`),
  por lo que hay que ejecutar desde este directorio o añadirlo al `PYTHONPATH`.

## Referencias

- D. P. Raymer, *Aircraft Design: A Conceptual Approach*, 6.ª y 7.ª ed.
  (Tablas 3.1, 3.2, 3.3, 5.3, 6.1, 6.3, 6.4; Fig. 8.2).
- CS-25 (EASA): factor Vref, 25.807 (salidas de emergencia).
- Documentos del curso en `../`: guion V2/DEF, cambios de Raymer v7 y
  `MTOW_A380_Raymer.pdf` (referencia de `a380-v2`).
