# sizing — Dimensionamiento preliminar de aviones de transporte a reacción

[![tests](https://github.com/voltia999/aircraft-sizing/actions/workflows/tests.yml/badge.svg)](https://github.com/voltia999/aircraft-sizing/actions/workflows/tests.yml)

Herramienta en Python para el dimensionamiento conceptual de un avión de
transporte siguiendo *Raymer, Aircraft Design: A Conceptual Approach*
(tablas estadísticas de la 6.ª y 7.ª edición). A partir de la misión y de unas
hipótesis aerodinámicas y de diseño calcula:

1. **Pesos**: MTOW (W0), peso en vacío y combustible, por iteración.
2. **Restricciones de carga alar**: W/S máximo por aterrizaje y por crucero.
3. **Ala**: superficie, envergadura, cuerdas y MAC.
4. **Fuselaje**: sección y longitud a partir de la distribución de cabina.
5. **Empenaje**: superficies de cola por coeficientes de volumen y superficies de mando.

Cada resultado se compara con los datos de un avión de referencia.

Todas las magnitudes están en SI; las **masas se expresan en kg** y la carga
alar en **kg/m²**.

---

## Primeros pasos

Requiere Python 3.10+. Desde este directorio:

```bash
pip install -r requirements.txt     # numpy y ambiance (ISA): lo justo para el cálculo
pip install -r requirements-dev.txt # además pytest, y jupyter para la notebook
python main.py                      # dimensiona el caso del guion V4 e imprime el informe
python example/a320_guion_v4.py     # el mismo caso, paso a paso frente al PDF del guion
jupyter notebook example/a320_guion_v4.ipynb   # el guion sección a sección, con sus ecuaciones
python -m pytest tests              # regresión contra los guiones
```

Para dimensionar tu propio avión, copia el ejemplo en `cases/` y cambia sus
entradas: lo explica [`cases/README.md`](cases/README.md). Allí está también
`a_380.py` (`python main.py a380`), un caso de dos cubiertas y cuatro motores
fuera del guion.

## Qué hay en cada carpeta

Cada carpeta tiene su propio README con el detalle.

| Carpeta | Qué contiene | Léelo si… |
|---|---|---|
| [`example/`](example/README.md) | El caso del guion V4, con una notebook que sigue el PDF sección a sección | empiezas: es la mejor forma de ver el método completo |
| [`cases/`](cases/README.md) | Tus casos de trabajo (no se versionan) y el ejemplo del A380 | quieres dimensionar otro avión |
| [`core/`](core/README.md) | Entradas (`Mission`, `Aerodynamics`, `Design`, `Reference`), `Result` y constantes | necesitas saber qué significa cada campo y sus unidades |
| [`methods/`](methods/README.md) | Aerodinámica, pesos (iteración de W0) y restricciones | quieres ver o cambiar una ecuación de Raymer |
| [`geometry/`](geometry/README.md) | Ala, fuselaje desde la cabina y empenaje | trabajas en la geometría |
| [`tests/`](tests/README.md) | Regresión contra los guiones V2 y V4 | cambias algo y quieres comprobar que no rompes nada |
| [`docs/`](docs/README.md) | Metodología en LaTeX/PDF | quieres la justificación de cada ecuación |

`main.py` es la línea de órdenes: descubre los casos, ejecuta el cálculo e
imprime el informe.

## Uso

Desde este directorio (los módulos se importan desde la raíz del repositorio):

```bash
python main.py                         # caso por defecto: guion-v4, cálculo refinado
python main.py guion-v4 --first-order  # método de primer orden (Tabla 3.1)
python main.py guion-v4 --edition 6    # fuerza la edición de Raymer (6 o 7)
python main.py guion-v4 --descent      # añade el segmento de descenso (--no-descent lo quita)
python main.py --help                  # lista los casos disponibles
```

Salida (extracto de `python main.py`):

```
Case: refined   Raymer edition: 7   Reference: guion V4 (segment reference)
                              computed             actual     error

Weights
----------------------------------------------------------------------
  MTOW                          71,936 kg          78,000    -7.8 %
  OEW                           39,781 kg
  ...
Wing
----------------------------------------------------------------------
  Area S                         119.9 m2           123.0    -2.5 %
  Span b                         33.75 m            34.00    -0.7 %
  ...
```

La columna *error* es `calculado / real − 1`; solo aparece cuando el caso
define el dato real correspondiente.

Desde Python:

```python
from main import run, report

out = run("guion-v4", refined=True)   # dict con weights, limits, wing, fuselage, tail...
print(out["weights"].w0)              # MTOW [kg]
report(out)
```

## Flujo de cálculo

`main.run()` encadena las carpetas en este orden:

```
case() ─► Mission, Aerodynamics, Design, Reference          core/
            │
            ├─► weight.resolve() ────────► W0, We/W0, Wf/W0   methods/
            ├─► constraints.*   ─────────► W/S máx.           methods/
            ├─► wing.wing_geometry(W0) ──► S, b, cuerdas, MAC geometry/
            ├─► fuselage.fuselage_geometry(decks) ─► Lf, sección
            └─► tail.tail_geometry(ala, Lf) ─► S_HT, S_VT, mandos
```

El empenaje se calcula el último porque necesita el ala (MAC, S, b) y la
longitud del fuselaje (que fija el brazo de cola).

---

## Limitaciones

- `Design.max_span` se pasa a `wing_geometry` pero **no se aplica**: la
  envergadura no se recorta al límite de la caja del aeropuerto.
- La restricción de crucero y `statistical_thrust_to_weight` se informan, pero
  no modifican el diseño: W/S y T/W son entradas de `Design`.
- `is_feasible` y `Design.table_6_1_metric` no se usan en el flujo principal.
- Los imports son relativos a la raíz (`from core.data import …`), así que hay
  que ejecutar desde este directorio o añadirlo al `PYTHONPATH`
  (`example/a320_guion_v4.py` se encarga de ello y funciona desde cualquier sitio).

Las limitaciones propias de la geometría están en
[`geometry/README.md`](geometry/README.md#limitaciones), y las diferencias con
el guion V4 en [`example/README.md`](example/README.md#diferencias-con-el-guion).

## Referencias

- D. P. Raymer, *Aircraft Design: A Conceptual Approach*, 6.ª y 7.ª ed.
  (Tablas 3.1, 3.2, 3.3, 5.3, 6.1, 6.3, 6.4, 6.5; Figs. 6.3 y 8.2).
- CS-25 (EASA): factor Vref, 25.807 (salidas de emergencia).
- Guiones del curso: V2 (Raymer 6.ª ed.) y V4 (7.ª ed., incluido en `docs/`).

## Licencia

[MIT](LICENSE). Los coeficientes y ecuaciones son los publicados por Raymer y
se citan con su tabla o ecuación. El guion V4 de `docs/` es material del
curso y no está cubierto por la licencia MIT.
