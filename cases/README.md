# cases — Tus casos de trabajo

Carpeta para tus propios aviones. Su contenido **no se versiona** (solo este
README y el ejemplo del A380), así que puedes probar lo que quieras sin afectar
al repositorio. Si un caso debe compartirse con todos, va en
[`example/`](../example/README.md).

## Ejemplo: `a_380.py`

Un caso fuera del guion, con dos cubiertas y cuatro motores:

```bash
python main.py a380
```

Sirve de modelo para un avión de dos cubiertas: cada `Deck` lleva su altura de
cabina, su espesor de suelo y, en la superior, las escaleras.

Fija el factor de Oswald con `Aerodynamics(oswald=0.80)`. Con su flecha
(Λ_BA > 30°), la correlación 12.49 de Raymer da e = 0,57, por debajo de la
banda típica de 0,70–0,85, y el MTOW sale en torno a 1 070 t frente a las
560 t reales. Con e = 0,80 sale unas 613 t (+9 %).

La envergadura no se recorta a los 80 m de la caja del aeropuerto, porque
`Design.max_span` todavía no se aplica.

## Crear un caso

1. Copia la plantilla:

   ```bash
   cp example/a320_guion_v4.py cases/mi_avion.py
   ```

2. En `cases/mi_avion.py`:
   - cambia `NAME` por el nombre que quieras usar en la línea de órdenes;
   - cambia las entradas de `case()`, que devuelve
     `(mission, aero, design, reference)`. Los campos están en
     [`core/README.md`](../core/README.md); la cabina se define con `Deck` y
     `SeatingZone` ([`geometry/README.md`](../geometry/README.md));
   - borra la parte del recorrido, de `# --- worked example` hacia abajo.

3. Ejecútalo. `main.py` lo encuentra solo, sin registrarlo en ningún sitio:

   ```bash
   python main.py mi-avion
   python main.py --help        # lista todos los casos disponibles
   ```

## Reglas

- Cualquier `.py` de esta carpeta con una función `case()` es un caso.
- El nombre es la variable `NAME` del módulo o, si no la tiene, el nombre del
  archivo con `-` en lugar de `_` (`mi_avion.py` → `mi-avion`).
- Dos casos con el mismo nombre (aquí o en `example/`) dan un error al arrancar.
- Convención: los comentarios `(H)` marcan hipótesis propias, no datos
  publicados.
- `Reference` es opcional en la práctica: un campo a `0.0` no se compara.
