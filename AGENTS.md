# AGENTS.md — App_Certificados

Greenfield repo. No code, no README, no manifests, no tests, not a git repo. Only data inputs exist.

## Sources of truth (read-only)

`Insumo/` contains the only verified inputs. Never edit in place; treat as immutable and write outputs to a new folder (e.g. `Salida/`).

- `Insumo/Maestro_Estudiantes.xlsx` — sheet `Estudiantes`, 24 rows. Cols: `Identificacion | Nombre_Completo | Correo | Programa | Cohorte`. All `Programa=Técnico en IA Aplicada`, `Cohorte=2026-A`.
- `Insumo/Registro_Evaluaciones.xlsx` — sheet `Evaluaciones`, 88 rows. Cols: `Identificacion | Programa | Modulo | Nota | Asistencia_Pct | Fecha_Cierre`. Join key to Maestro is `Identificacion` (string; leading zeros possible — never cast to int).
- Coverage is uneven: Módulos 1–3 have 24 rows each, Módulo 4 has only 16. `Nota`/`Asistencia_Pct` span 0–100 (zeros present). Any pass/fail or certificate-eligibility threshold is **undefined** — do not invent one; ask the user.

## Environment gotchas

- Windows + OneDrive path with spaces and `ó` (`Proyectos Módulo II`). Always quote full paths in PowerShell; `head`/`grep`/`pip` bare commands don't exist here.
- Python runs via the `py` launcher (`py -c`, `py -m pip ...`), not `python3`/`pip`. `openpyxl` is not preinstalled: `py -m pip install openpyxl`.
- Spanish accents (`Técnico`, `Módulo`) render as `T�cnico` in this console's codepage. The data is fine — read/write with UTF-8 and don't "fix" the strings.
- No `AGENTS.md` predecessors, CI, lint, or test config exist. Don't assume tooling; confirm stack with the user before scaffolding the app.
