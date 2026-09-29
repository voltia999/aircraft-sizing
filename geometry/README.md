# geometry — Ala, fuselaje y empenaje

Paquete que convierte el MTOW (W0) y las decisiones de `Design` en geometría.
Se usa en este orden, porque cada módulo depende del anterior:

```
wing.wing_geometry(W0, aero, design)            ─► S, b, MAC ...
fuselage.fuselage_geometry(design.decks, ...)   ─► longitud Lf, sección ...
tail.tail_geometry(ala, Lf, coeficientes)       ─► S_HT, S_VT, mandos
```

El empenaje va el último: necesita la MAC, S y b del ala y la longitud del
fuselaje, que fija el brazo de cola.

Todas las longitudes están en **m**, las superficies en **m²** y los ángulos de
entrada en **grados**, salvo `Aerodynamics.sweep_c4`, que va en radianes. Las
funciones devuelven `dict` planos para que `main.report()` pueda leerlos por clave.

---

## `wing.py` — ala trapezoidal

### `wing_geometry(w0, aero, design, max_span=None) -> dict`

| Entrada | Uso |
|---|---|
| `w0` | MTOW [kg] |
| `aero.AR`, `aero.taper_ratio` | Alargamiento y estrechamiento λ |
| `design.wing_loading` | W0/S [kg/m²] |
| `max_span` | Se acepta pero **no se aplica** (ver *Limitaciones*) |

Ecuaciones:

```
S      = W0 / (W0/S)
b      = √(AR · S)
c_root = 2S / (b (1 + λ))
c_tip  = λ · c_root
MAC    = ⅔ · c_root · (1 + λ + λ²) / (1 + λ)
```

Devuelve `{"S", "b", "AR", "c_root", "c_tip", "MAC"}`. `AR` se recalcula como
b²/S, así que coincide con el de entrada; se incluye para que se pueda comparar
cuando se limite la envergadura.

Ejemplo (guion V2, W0 = 72 000 kg, W/S = 600, AR = 9.5, λ = 0.24):
S = 120 m², b = 33.76 m, c_root = 5.73 m, c_tip = 1.38 m, MAC = 4.00 m.

---

## `fuselage.py` — fuselaje desde la cabina

El fuselaje se dimensiona de dentro hacia fuera: primero la cabina y después la
estructura, el morro y el cono de cola. W0 solo interviene en la comprobación
estadística.

### Modelo de cabina

**`SeatingZone`**: una zona homogénea de asientos (una clase).

| Campo | Defecto | Descripción |
|---|---|---|
| `name` | — | Nombre de la clase (`"business"`, `"economy"`…) |
| `seats_abreast` | — | Asientos por fila |
| `n_seats` | — | Número de asientos |
| `seat_width` | 0.46 m | Ancho de asiento |
| `seat_pitch` | 0.81 m | Paso entre filas |
| `aisles` | 2 | Informativo; el ancho usa `Deck.aisles` |
| `pax_per_lavatory` | `None` | Pasajeros por lavabo; `None` toma el valor de la cubierta |

Propiedades: `n_rows = ⌈n_seats / seats_abreast⌉` y `length = n_rows · seat_pitch`.

**`Deck`**: una cubierta de pasajeros (zonas + servicios).

| Campo | Defecto | Descripción |
|---|---|---|
| `name` | — | `"main"`, `"upper"`… |
| `zones` | — | Lista de `SeatingZone` |
| `aisles` | 2 | Número de pasillos |
| `n_staircases` | 0 | Escaleras entre cubiertas |
| `pax_per_galley_module` | 100 | Pasajeros por módulo de galley |
| `pax_per_lavatory` | 50 | Pasajeros por lavabo (por defecto) |
| `cabin_height` | 2.30 m | Altura libre de cabina |
| `floor_thickness` | 0.25 m | Espesor del suelo |

Propiedades: `n_seats` (suma de las zonas); `seats_abreast` y `seat_width`
(máximo de las zonas, porque la zona más ancha fija el ancho de la cabina).

Ejemplo:

```python
from geometry.fuselage import Deck, SeatingZone

main = Deck("main", aisles=1, zones=[
    SeatingZone("business", n_seats=12,  seats_abreast=4, seat_pitch=0.97),
    SeatingZone("economy",  n_seats=138, seats_abreast=6, seat_pitch=0.81),
])
```

### Constantes

| Constante | Valor | Significado |
|---|---|---|
| `AISLE_WIDTH` | 0.51 m | Ancho por pasillo |
| `CLEARANCE_PER_SEAT` | 0.05 m | Reposabrazos y holgura lateral por asiento |
| `LD3_HEIGHT` | 1.63 m | Contenedor LD3 (fuselaje ancho) |
| `LD3_45_HEIGHT` | 1.14 m | Contenedor LD3-45 (fuselaje estrecho) |
| `LAVATORY_LENGTH` | 0.95 m | Longitud de un lavabo |
| `GALLEY_MODULE` | 0.90 m | Longitud de un módulo de galley |
| `EXIT_PAIR_LENGTH` | 1.10 m | Vestíbulo por par de puertas |
| `STAIRCASE_LENGTH` | 1.50 m | Longitud por escalera |
| `PAX_PER_TYPE_A_PAIR` | 110 | Pasajeros por par de salidas tipo A (CS 25.807) |

### Sección transversal

| Función | Cálculo |
|---|---|
| `cabin_width(deck)` | n·seat_width + aisles·0.51 + n·0.05 |
| `external_width(deck, structure_per_side=0.10)` | cabin_width + 2·estructura |
| `hold_height(container_height=LD3_HEIGHT, clearance=0.10)` | contenedor + holgura (LD3 → 1.73 m, LD3-45 → 1.24 m) |
| `section_height(decks, keel=0.20, crown=0.35, hold=None)` | quilla + bodega + Σ(suelo + cabina) + corona |
| `equivalent_diameter(width, height)` | √(ancho · alto), para secciones no circulares (Raymer) |

### Longitud

| Función | Cálculo |
|---|---|
| `required_exit_pairs(n_seats)` | ⌈n_seats / 110⌉ |
| `deck_length(deck)` | Desglose de la cubierta (ver abajo) |
| `nose_length(height, radome_height=1.00, upper_angle=20, lower_angle=15)` | (h − h_radomo) / (tan θ_sup + tan θ_inf) |
| `tailcone_length(height, end_height=0.80, upper_angle=11, lower_angle=15)` | (h − h_final) / (tan θ_sup + tan θ_inf) |
| `fineness_ratio(length, diameter)` | L / D (óptimo subsónico 6–8) |
| `statistical_length(w0, edition=7)` | Raymer Tabla 6.3: Lf = a·W0^C1 |

`deck_length` devuelve `{"seating", "galleys", "lavatories", "exits", "stairs", "total"}`:

- `seating`: Σ filas · paso de cada zona.
- `galleys`: ⌈n_seats / pax_per_galley_module⌉ · 0.90.
- `lavatories`: Σ por zona de ⌈n_seats_zona / pax_per_lavatory⌉ · 0.95.
  El redondeo es **por zona**, no global.
- `exits`: pares de salidas tipo A · 1.10.
- `stairs`: n_staircases · 1.50.

Los ángulos del morro y del cono de cola siguen el criterio de contorno de
Raymer (Fig. 8.2). Delante se admiten ángulos mayores porque el gradiente de
presión es favorable. Detrás, la desviación respecto a la corriente libre debe
quedarse en 10–12° (hasta 15° por debajo) para que el flujo no se desprenda.

Coeficientes de la Tabla 6.3 (métrico, transporte a reacción):

| Edición | a | C1 |
|---|---|---|
| 6 | 0.287 | 0.43 |
| 7 | 0.690 | 0.360 |

### `fuselage_geometry(decks, w0=None, **kwargs) -> dict`

Ensambla todo el fuselaje:

1. La cubierta más larga es la **dimensionante**.
2. Sección: con `diameter` se usa una sección circular fija; si no, se usa el ancho
   exterior de la cubierta dimensionante y la altura apilando todas las cubiertas.
3. Longitud = cabina de la cubierta dimensionante + morro + cono de cola.
4. Si se pasa `w0`, añade `statistical_length` como comprobación.

`kwargs` opcionales (normalmente vienen de `Design.fuselage`):

| Clave | Efecto |
|---|---|
| `diameter` | Fija la sección circular [m] |
| `nose`, `tailcone` | Fija sus longitudes [m] |
| `structure_per_side`, `keel`, `crown`, `hold` | Parámetros de la sección |
| `edition` | Edición de la Tabla 6.3 (defecto 7) |

Devuelve:

| Clave | Descripción |
|---|---|
| `cabin_widths` | `{nombre_cubierta: ancho interior}` |
| `external_width`, `section_height`, `equivalent_diameter` | Sección [m] |
| `deck_lengths` | `{nombre_cubierta: desglose de deck_length}` |
| `cabin_length`, `nose`, `tailcone`, `length` | Longitudes [m] |
| `fineness` | Esbeltez L / D_eq |
| `statistical_length` | Solo si se pasa `w0` |

Ejemplo, con la cubierta anterior y los valores fijados por el guion V2:

```python
fuselage_geometry([main], diameter=3.95, nose=4.0, tailcone=5.0)["length"]   # 38.34 m
```

Sin fijar nada, la sección sale de 3.77 × 4.83 m (D_eq = 4.27 m), el morro de
6.06 m y el cono de 8.72 m, lo que da Lf = 44.1 m. Por eso en narrow-bodies
conviene fijar `diameter`, `nose` y `tailcone`.

---

## `tail.py` — empenaje por coeficientes de volumen

### Constantes

| Constante | Valor | Fuente |
|---|---|---|
| `C_HT_JET_TRANSPORT` | 1.00 | Raymer Tabla 6.4 |
| `C_VT_JET_TRANSPORT` | 0.09 | Raymer Tabla 6.4 |
| `ARM_FRACTION_WING_ENGINES` | 0.50 | Brazo / Lf, motores en el ala (0.50–0.55) |
| `ARM_FRACTION_AFT_ENGINES` | 0.45 | Brazo / Lf, motores traseros (0.45–0.50) |
| `AILERON_CHORD_RATIO` | 0.23 | c_a/c, Raymer fig. 6.3 con envergadura 0.4 |
| `AILERON_SPAN` | (0.50, 0.90) | Tramo de semienvergadura de los alerones (Raymer 6.6) |
| `ELEVATOR_CHORD_RATIO` | 0.25 | c_e/c, Raymer tabla 6.5 (transporte a reacción) |
| `RUDDER_CHORD_RATIO` | 0.32 | c_r/c, Raymer tabla 6.5 |

### `ControlSurfaceRatios`

Dataclass con `aileron_chord`, `aileron_span`, `elevator_chord` y `rudder_chord`,
con los valores de Raymer por defecto. Los mandos mantienen la cuerda relativa
constante (Raymer 6.6), así que en los timones la fracción de área es la de cuerda.

### `TailCoefficients`

Dataclass con `c_ht`, `c_vt` y `arm_fraction`, que por defecto toman los valores
de Raymer. Se pueden bajar en aviones grandes fly-by-wire con estabilidad
relajada: el A380 trabaja con c_HT ≈ 0.6–0.7.

### Funciones

| Función | Cálculo |
|---|---|
| `tail_arm(fuselage_length, coeffs)` | L = arm_fraction · Lf (de c/4 del ala a c/4 de la cola) |
| `horizontal_tail_area(mac, wing_area, arm, c_ht)` | S_HT = c_HT · MAC · S / L |
| `vertical_tail_area(span, wing_area, arm, c_vt)` | S_VT = c_VT · b · S / L |
| `span_area_fraction(taper, eta_in, eta_out)` | Fracción del área del ala trapezoidal entre dos estaciones de semienvergadura |
| `control_surfaces(wing, s_ht, s_vt, ratios=None)` | Alerones = c_a/c · fracción(0.5–0.9) · S; timones = c/c · S_cola |
| `implied_coefficients(s_ht, s_vt, mac, span, wing_area, arm)` | Método inverso: `{"c_ht", "c_vt"}` de un avión real |
| `tail_geometry(wing, fuselage_length, coeffs=None)` | Ensamblado completo |

La cola vertical usa la **envergadura** como longitud de referencia, no la MAC,
porque los momentos de guiñada que compensa (por ejemplo, con un motor parado)
escalan con b.

`tail_geometry` recibe el `dict` de `wing_geometry` (usa `S`, `b`, `MAC`, `c_root` y `c_tip`) y
devuelve `{"arm", "s_ht", "s_vt", "controls"}`.

Ejemplo (guion V2: ala anterior, Lf = 37.5 m, brazo 0.40·Lf = 15 m):
S_HT = 32.0 m², S_VT = 24.3 m². El guion toma alerones del 5 % de S y timones del
30 %: 6.0, 9.6 y 7.3 m². Con los valores de Raymer (λ = 0.24) salen 8.3, 8.0 y 7.8 m².

```python
from geometry import tail
t = tail.tail_geometry(w, 37.5, tail.TailCoefficients(arm_fraction=0.40))
```

`implied_coefficients` se usa en `main.report()` para ver cuánto se alejan los
coeficientes medios de Raymer de las superficies reales del avión de referencia.

---

## Limitaciones

- `wing_geometry` ignora `max_span`: la envergadura no se recorta al límite
  del aeropuerto (código C, E o F de la OACI).
- El ala es trapezoidal simple: sin quiebro (*kink*) ni winglets.
- `fuselage_geometry` solo usa la cubierta más larga para la longitud; las
  cubiertas superiores cortas solo cuentan en la altura de la sección.
- El redondeo de lavabos por zona da uno más que el guion V2 en el caso de 150
  plazas (4 frente a 3). Por eso fallan `test_cabin_length` y `test_fuselage_length`.
- `SeatingZone.aisles` no se usa; el ancho de cabina toma los pasillos de `Deck`.
