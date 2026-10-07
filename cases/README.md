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

### Limitaciones

El A380 está **fuera del rango de datos** con los que Raymer ajustó sus
correlaciones: pesa un 40 % más que cualquiera de ellos. Es un ejemplo del
modelo de dos cubiertas, no una validación del método. Frente al A380-800 real:

| Magnitud | Código | Real | Error | Causa |
|---|---|---|---|---|
| MTOW | 613 t | 560 t | +9,5 % | Errores que se compensan (ver abajo) |
| We/W0 | 0,453 | 0,495 | −8 % | La Tabla 6.1 extrapola mal a este tamaño |
| L/D de crucero | 16,7 | ~19–20 | −15 % | `swet_sref = 6` (valor típico de Raymer); por componentes, el A380 ronda 4,5 |
| Superficie alar | 943 m² | 845 m² | +12 % | S = W0 / (W/S), arrastra el error de W0 |
| Envergadura | 84,3 m | 79,8 m | +6 % | Ídem, y `Design.max_span` aún no recorta a los 80 m de la caja del aeropuerto |
| Empuje | 1 504 kN | 1 240 kN | +21 % | T/W = 0,25 elegido (real 0,226) por un W0 más alto |
| Colas | 325 / 194 m² | 206 / 122 m² | +58 % | Tabla 6.4: c_HT = 1,00 y c_VT = 0,09; el A380 real tiene 0,63 y 0,057 (fly-by-wire, avión muy grande) |
| Sección del fuselaje | 6,32 × 7,23 m | 7,14 × 8,41 m | −11 % / −14 % | El modelo suma asientos y apila cubiertas en línea recta; el A380 es un óvalo con paredes curvas |

**El MTOW parece bueno por casualidad.** La ecuación de pesos queda muy cerca
de no cerrar: 1 − W_f/W0 − W_e/W0 = 0,082, frente a 0,22 en el guion V4, así
que cada punto de fracción se amplifica unas 12 veces. Dentro hay dos errores
de signo contrario: la fracción en vacío sale baja y la de combustible alta. Y
el resultado depende muchísimo de hipótesis que el caso no justifica:

| Cambio | MTOW |
|---|---|
| Caso actual | 613 t (+9,5 %) |
| TSFC de crucero 0,55 h⁻¹ en lugar de 0,5 (por defecto) | 883 t (+58 %) |
| `swet_sref` = 5 en lugar de 6 | 450 t (−20 %) |
| `swet_sref` = 4,5 | 396 t (−29 %) |
| Oswald de la correlación 12.49 (e = 0,57) | ~1 070 t (+90 %) |

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
