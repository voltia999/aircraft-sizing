# Ejemplo: guion V4 paso a paso

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
| Alerones | 9,2 m² | 6,6 m² | El código integra la banda del 50–90 % de la semienvergadura con c_a/c = 0,23 (Fig. 6.3); el guion toma el 5 % de S. |
| W/S óptima de crucero | 356 kg/m² | 365 kg/m² | El guion redondea CD0 a 0,016 (es 0,0156). |

Las colas usan el brazo sobre la longitud estadística (Tabla 6.3), como el
guion, con `Design.tail_arm_length = "statistical"`.
