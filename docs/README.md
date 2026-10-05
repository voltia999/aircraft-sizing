# docs — Metodología

| Archivo | Contenido |
|---|---|
| `metodologia.tex` / `metodologia.pdf` | Metodología implementada en el código, con las ecuaciones y su referencia en Raymer (6.ª y 7.ª ed.) |
| `Dimensionamiento_preliminar_aeronave_Raymer_V4.pdf` | Guion V4 del curso, que reproducen [`example/`](../example/README.md) y `tests/test_guion_v4.py`. Es material del curso y no se versiona: cópialo aquí si lo tienes |

`metodologia.pdf` se versiona; los archivos auxiliares de LaTeX están en
`.gitignore`. Para recompilarlo después de editar el `.tex`:

```bash
cd docs
latexmk -pdf metodologia.tex
```

Si cambias un método en `methods/` o `geometry/`, actualiza también su sección
en `metodologia.tex` y vuelve a compilar el PDF.
