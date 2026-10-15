# PLAN.md — App_Certificados (Academia Horizonte)

Construcción por etapas: validar cruce → backend Flask → interfaz.
No se avanza de etapa sin su validación en verde. Modo Plan: sin código hasta aprobar cada etapa.

## Etapa 1 — Validar el cruce de datos
- Objetivo: confirmar que los Excel se leen bien y las reglas R1–R6 dan las cifras de control.
- Qué incluye: lectura de `Insumo/Maestro_Estudiantes.xlsx` (hoja `Estudiantes`) y `Insumo/Registro_Evaluaciones.xlsx` (hoja `Evaluaciones`); normalización de `Identificacion` a texto (`strip()` + quitar `.0`); agrupado por (identificacion, programa); promedios con 2 decimales; clasificación R3–R5 e inconsistencias R6.
- Validación: `uv run python -c "from models.certificados import obtener_resumen_completo; print(obtener_resumen_completo()['contadores'])"` debe dar `{'aprobacion': 19, 'participacion': 3, 'sin_certificado': 1, 'total_inconsistencias': 3}`; controles `101230456` → 91.25/96.25 y Acuña Blanco → 72.0/81.67; BD con 24 estudiantes y 88 evaluaciones.
- Criterio de avance: cifras exactas y los 3 casos borde detectados (Javier `304560321` sin evaluaciones, `999880777` sin maestro, Zúñiga 36.25%).

## Etapa 2 — Backend con Flask
- Objetivo: servidor funcional con datos reales y descarga de certificados.
- Qué incluye: `app.py` (solo crea app y registra blueprints); `models/datos.py` (único acceso a BD, SQLite local o Postgres si hay `DATABASE_URL`); `models/certificados.py` (R1–R6); `services/carga_excel.py` y `services/generador_pdf.py`; rutas `/`, `/certificado/<id>/<programa>`, `/descargar-todos`; **crear el route `/cargar` (GET + POST) que hoy falta** aunque `cargar.html` y el nav ya lo piden.
- Validación: `uv run python app.py` levanta en puerto 5000; `/` muestra contadores 19/3/1/3; `/certificado/101230456/<programa>` devuelve PDF; `/descargar-todos` devuelve `.zip` con 22 PDFs; `/cargar` acepta los dos Excel y recarga la BD.
- Criterio de avance: las 4 rutas responden y el `.zip` trae exactamente los 22 emitibles (Fernanda excluida).

## Etapa 3 — Interfaz
- Objetivo: tablero usable con diseño azul marino `#14213D` y dorado `#B8923D`.
- Qué incluye: `views/base.html`, `views/tablero.html` (KPIs, tabla con buscador, sección R6), `views/cargar.html` (formulario de 2 archivos), `views/static/css/estilos.css` (único CSS vivo; ignorar `static/` raíz).
- Validación: revisión visual del tablero; tabla filtra por cédula/nombre; estados y botones coinciden con `puede_descargar`; cierre con subagentes `.agents/agents/`: `tester-datos` (cifras) y `revisor` (MVC + sin secretos).
- Criterio de avance: informe `tester-datos` todo verde e informe `revisor` sin hallazgos críticos.

## Decisiones técnicas (resumen)
- Librerías: `pandas` + `openpyxl` (lectura y agregados), `flask` (servidor), `fpdf2` (PDF A4 horizontal), `psycopg[binary]` (Supabase, `prepare_threshold=None`), `python-dotenv` (`DATABASE_URL`). Instalación solo con `uv sync`; nunca `pip`.
- Estructura MVC: `app.py` sin lógica; `models/` decide y guarda; `services/` transforma y genera; `controllers/` rutea; `views/` muestra. Detalle en `AGENTS.md`.
