# cases — Tus casos de trabajo

Carpeta para tus propios aviones. Su contenido **no se versiona** (solo este
README), así que puedes probar lo que quieras sin afectar al repositorio. Si un
caso debe compartirse con todos, va en [`example/`](../example/README.md).

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
