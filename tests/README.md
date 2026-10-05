# tests — Regresión contra los guiones

```bash
python -m pytest tests          # todos
python -m pytest tests -k v4    # solo el guion V4
```

`conftest.py` añade la raíz del repositorio al `sys.path`, así que los tests
importan los módulos igual que `main.py`.

| Archivo | Qué comprueba |
|---|---|
| `test_guion_v4.py` | `docs/Dimensionamiento_preliminar_aeronave_Raymer_V4.pdf` (Raymer 7.ª ed.), ecuación a ecuación |
| `test_guion_v2.py` | `Dimensionamiento_preliminar_aeronave_Raymer_V2.pdf` (Raymer 6.ª ed.) |
| `test_controls_loiter.py` | Espera con la polar, superficies de mando (Fig. 6.3, Tabla 6.5) y rango de Oswald, calculados a mano |
| `test_raymer_options.py` | Contra el libro: Tabla 6.1 en unidades fps, factor de compuestos y reducciones de cola de la sección 6.4 |
| `test_case_options.py` | Que las opciones que fija un caso (`Design.tail`, `Design.controls`, estándares de cabina de `Deck`, ángulos de morro y cola) llegan al resultado, y que una opción de fuselaje mal escrita da error |

Los tests de los guiones usan una tolerancia relativa del 1 %, porque los PDF
redondean a unas tres cifras significativas.

## `test_guion_v4.py`

Usa el `case()` de `example/a320_guion_v4.py`, así que el ejemplo y los tests
no pueden separarse. Las magnitudes del guion que dependen del W0 refinado se
evalúan en su W0 (79 800 kg), y `test_guion_refined_w0` reconstruye ese W0 con
la fracción de combustible del guion.

`test_code_refined_w0` no viene del PDF: fija el W0 refinado del propio código
(71 936 kg) para detectar cambios no intencionados. Si cambias el método a
propósito, actualiza ese valor.

## Fallos conocidos

Estado actual: **66 correctos y 3 fallos esperados** (`xfail`), todos del V2.
Están marcados con `@pytest.mark.xfail(strict=True, reason=...)`: pytest los
cuenta como esperados y, si algún día pasan, lo avisa como error para que se
quite la marca.

- `test_cabin_length`: el guion usa 3 lavabos para 150 plazas (uno cada 50); el
  código redondea por zona (12/50 → 1, 138/50 → 3) y obtiene 4, así que la
  cabina sale 0.95 m más larga.
- `test_fuselage_length`: consecuencia del anterior (38.34 m frente a 37.5 m).
- `test_refined_w0`: el código usa la W/S real a mitad de crucero para la L/D
  de la polar y la (L/D)max de la polar en la espera; el guion V2 usa la W/S de
  diseño y la espera de primer orden. Además, el guion aplica la Tabla 6.1 de
  la 6.ª edición como si estuviera en kg, cuando el libro la da en lb y lb/ft²
  (65 700 kg frente a 72 000 kg).

Si añades un test que falla a propósito por una diferencia de método con el
guion, documéntalo aquí.
