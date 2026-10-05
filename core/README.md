# core — Entradas, salidas y constantes

Las estructuras de datos que comparten todos los módulos. No calculan nada:
un caso (`example/` o `cases/`) rellena las cuatro dataclasses de `data.py` y
`methods/` y `geometry/` las leen.

| Archivo | Contenido |
|---|---|
| `data.py` | `Mission`, `Aerodynamics`, `Design`, `Reference` (entradas) |
| `results.py` | `Result` (salida de la iteración de pesos) |
| `constants.py` | Constantes físicas y conversiones de unidades |

Todas las magnitudes están en SI; las **masas se expresan en kg** y la carga
alar en **kg/m²**.

---

## `data.py`

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
| `sweep_c4` | 25° | Flecha en c/4 (**en radianes**: `radians(25)`) |
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
| `max_span` | `None` | Límite de envergadura del aeropuerto (m); **no se aplica todavía** |
| `decks` | `[]` | Lista de `Deck` (distribución de cabina, ver [`geometry/`](../geometry/README.md)) |
| `fuselage` | `{}` | Opciones de `fuselage_geometry`: valores fijados (`diameter`, `nose`, `tailcone` [m]), parámetros de la sección y ángulos de morro y cola. Una clave desconocida da error. Lista completa en [`geometry/`](../geometry/README.md#fuselage_geometrydecks-w0none-kwargs---dict) |
| `tail` | `TailCoefficients()` | c_HT = 1.00, c_VT = 0.09 (Tabla 6.4) y brazo / Lf = 0.50 |
| `controls` | `ControlSurfaceRatios()` | Cuerdas relativas de alerones (0.23, tramo 0.5–0.9), timón de profundidad (0.25) y de dirección (0.32) |
| `tail_arm_length` | `"cabin"` | Longitud que fija el brazo: `"cabin"` (disposición de cabina) o `"statistical"` (Tabla 6.3) |

Los valores por defecto de `tail`, `controls` y de los estándares de cabina de
`Deck` son los de Raymer para transporte a reacción. Cámbialos **en el caso**,
nunca en los módulos: así afectan solo a ese avión.

```python
from geometry.tail import TailCoefficients

design = Design(
    ...,
    tail=TailCoefficients(c_ht=0.65, c_vt=0.07, arm_fraction=0.50),  # A380, fly-by-wire
)
```

### `Reference` — avión real (solo validación)

Datos publicados (MTOW, OEW, MLW, superficie alar, envergadura, dimensiones de
fuselaje, superficies de cola, empuje…). Un campo a `0.0` significa "sin dato"
y no se compara en el informe. Las propiedades `wing_loading` y
`thrust_to_weight` se derivan de los demás campos.

---

## `results.py`

`Result` es lo que devuelve `methods.weight.resolve()`:

| Campo / propiedad | Descripción |
|---|---|
| `w0` | MTOW convergido [kg] |
| `wf_w0`, `we_w0` | Fracciones de combustible y de peso en vacío |
| `history` | Iteraciones `(W0, We/W0, W0 nuevo)` |
| `w_empty`, `w_fuel` | We y Wf [kg] |

---

## `constants.py`

| Constante | Valor | Uso |
|---|---|---|
| `G` | 9.81 m/s² | Gravedad |
| `RHO_SL` | 1.225 kg/m³ | Densidad ISA a nivel del mar (aterrizaje) |
| `NM` | 1852 m | Millas náuticas → m |
| `KT` | 0.514444 m/s | Nudos → m/s |
| `HOUR` | 3600 s | Consumos en h⁻¹ → s⁻¹ |
| `LB`, `FT2` | 2.20462, 10.7639 | kg → lb y m² → ft² (Tabla 6.1 de la 7.ª ed.) |
