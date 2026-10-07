# Ejemplo: guion V4 paso a paso

Hay dos formas de recorrer el guion:

| Archivo | Para qué |
|---|---|
| `a320_guion_v4.ipynb` | **El guion con el código**: sigue el PDF sección a sección (1.3 a 11) con sus títulos, ecuaciones y explicaciones, define las entradas en `Mission`, `Aerodynamics` y `Design`, y compara cada valor del código con el del guion. Es el mejor punto de partida |
| `a320_guion_v4.py` | El caso (`case()`) y el mismo recorrido en texto para la terminal, sin explicaciones |

## `a320_guion_v4.ipynb`

La notebook se ve ya ejecutada en GitHub. Para ejecutarla tú:

```bash
pip install -r requirements-dev.txt
jupyter notebook example/a320_guion_v4.ipynb   # o ábrela en VS Code
```

Se limita a lo que aparece en el PDF: no tiene gráficas ni estudios de
sensibilidad. Cada celda de cálculo imprime el valor del código, el del guion y
el error relativo:

```
                                        código              guion   error
S (23)                                   119.9 m2           120.0    -0.1%
b (24)                                   33.75 m            33.70    +0.1%
```

Termina con la Tabla 7 del guion: código, guion y avión de referencia.

Las entradas se escriben a mano en la notebook, para que se vea cómo se define
un caso; son las mismas que las de `a320_guion_v4.py`, así que si cambias una
cambia también la otra. Desde la sección 8.12 usa el W0 refinado del guion,
calculado con `guion_refined_w0` del propio script (ver
[Diferencias con el guion](#diferencias-con-el-guion)).

## `a320_guion_v4.py`

`a320_guion_v4.py` reproduce
`docs/Dimensionamiento_preliminar_aeronave_Raymer_V4.pdf` (narrow-body de 150
plazas, Raymer 7.ª ed.). El archivo es a la vez:

- **un caso**: la función `case()` con todas las entradas del guion, comentadas
  con la sección del PDF de la que salen. `main.py` lo encuentra solo:

  ```bash
  python main.py guion-v4                 # informe completo
  python main.py guion-v4 --first-order   # método de primer orden
  ```

- **un recorrido paso a paso**: cada sección del guion llama a las funciones de
  `weight`, `aerodynamic`, `constraints` y `geometry`, e imprime el valor del
  código junto al del PDF y el error relativo:

  ```bash
  python example/a320_guion_v4.py
  ```

  ```
                                          code              guion  error
  6-7  Empty fraction and W0 (first order, Table 3.1)
  ------------------------------------------------------------------
    W0 (17)                             71,940 kg          72,000   -0.1%
    We/W0                                0.537              0.537   +0.1%
  ```

`tests/test_guion_v4.py` usa este mismo `case()`, así que si un cambio en el
código rompe el ejemplo, los tests fallan.

## Usarlo como plantilla

Para dimensionar otro avión, copia `a320_guion_v4.py` en `cases/` con otro
nombre, cambia `NAME` y las entradas de `case()`, y borra la parte del
recorrido (de `# --- worked example` hacia abajo). `main.py` lo detecta sin
registrarlo en ningún sitio. Los pasos completos están en
[`cases/README.md`](../cases/README.md).

## Diferencias con el guion

Todo coincide con el PDF dentro del 1 % salvo:

| Magnitud | Código | Guion | Motivo |
|---|---|---|---|
| W0 refinado | 71 936 kg | 79 800 kg | El guion multiplica la L/D de la polar (ya en condición de crucero, Raymer 6.3.7) otra vez por 0,866 y mantiene la espera de primer orden. Reconstruyendo su fracción de combustible con las mismas funciones (`guion_refined_w0`) sale 79 255 kg. |
| Longitud de cabina | 29,34 m | 28,45 m | Los lavabos se redondean por clase (1 + 3); el guion usa 3 para las 150 plazas. |
| W/S óptima de crucero | 356 kg/m² | 365 kg/m² | El guion redondea CD0 a 0,016 (es 0,0156). |

Las colas usan el brazo sobre la longitud estadística (Tabla 6.3), como el
guion, con `Design.tail_arm_length = "statistical"`, y los alerones son el 5 %
de S, también como el guion, con `ControlSurfaceRatios(aileron_area_fraction=0.05)`.
