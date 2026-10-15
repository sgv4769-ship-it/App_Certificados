# AGENTS.md — App_Certificados (Academia Horizonte)

Flask con `uv` que emite certificados por reglas fijas. Sin IA. Sin tests, lint ni CI.

Somos Academia Horizonte: formamos programas técnicos a empresas y al cerrar cada cohorte emitimos un certificado por estudiante. Hoy el proceso es manual en Excel y Word; esta app web lo automatiza.

Plan por etapas en `PLAN.md`: 1) validar cruce de datos, 2) backend Flask, 3) interfaz. No avanzar de etapa sin validación verde.

## Comandos (`uv`, nunca `pip`)
- Instalar: `uv sync` · Servidor: `uv run python app.py` (puerto 5000, variable `app` en `app.py`) · Cargar Excel a BD: `uv run python services/carga_excel.py`
- Deploy: `vercel.json` apunta a `app.py`.
- Verificación rápida: `uv run python -c "from models.certificados import obtener_resumen_completo; print(obtener_resumen_completo()['contadores'])"` → `{'aprobacion': 19, 'participacion': 3, 'sin_certificado': 1, 'total_inconsistencias': 3}`

## Arquitectura MVC (respetarla)
- `app.py`: solo crea `Flask(__name__, template_folder="views", static_folder="views/static")` y registra `tablero_bp` + `certificados_bp`. Sin lógica.
- `models/datos.py`: ÚNICO que toca la BD. Postgres/Supabase solo si `DATABASE_URL` empieza con `postgresql://` o `postgres://` (con `psycopg.connect(..., prepare_threshold=None)` por el pooler); si no, SQLite `certificados.db` (en `.gitignore`, no commitear).
- `models/certificados.py`: reglas R1–R6. Constantes `NOTA_MINIMA=70`, `ASISTENCIA_MINIMA=80`, `ASISTENCIA_CRITICA=50` (límites inclusivos).
- `services/carga_excel.py`: lee hojas `Estudiantes`/`Evaluaciones`, normaliza `Identificacion` a texto (`strip()` + quita `.0`). Acepta carpetas `insumos|Insumo|Insumos`; la real es `Insumo/`.
- `services/generador_pdf.py`: fpdf2, A4 horizontal, `#14213D` / `#B8923D`.
- `controllers/` solo rutas, `views/` solo Jinja (muestra, no calcula ni decide). Flask sirve `views/static`; el duplicado `static/` de la raíz está muerto (idéntico hoy, no lo uses).
- Rutas reales: `/`, `/certificado/<identificacion>/<path:programa>`, `/descargar-todos`. ⚠️ `/cargar` NO existe (nav, `tablero.html` y form POST de `cargar.html` apuntan a nada) — hay que crearlo.

## Datos y reglas (verificado en código y BD: 24 estudiantes, 88 evaluaciones)
- R1 agrupa por (identificacion, programa): un certificado por estudiante y programa. R2: promedio = media de `nota` (0-100), asistencia = media de `asistencia_pct`, 2 decimales. R3 Aprobación ≥70 y ≥80. R4 Participación <70 y ≥80. R5 Sin certificado si asistencia <80.
- R6 (`puede_descargar=False`): maestro sin evaluaciones; evaluaciones sin maestro; asistencia <50. El caso <50 también cuenta en Sin certificado y sale en ambas listas.
- Controles: `101230456` → 91.25/96.25 Aprobación; Acuña Blanco → 72.0/81.67 Aprobación; `304560321` sin evaluaciones; `999880777` sin maestro; Zúñiga 36.25%.

## Restricciones
- Nunca modificar `Insumo/`. Nunca leer ni mostrar `.env` (ver solo `.env.ejemplo`); nunca hardcodear secretos.
- Español sencillo: explica lo que vas haciendo paso a paso. Código simple y comentado, señalando los ladrillos (variables, tipos, condicionales, bucles, funciones). Diseño azul marino y dorado. Plan corto antes de construir; entregas pequeñas por capa.
- Al cerrar: `.agents/agents/` — `tester-datos` valida cifras (solo lectura/ejecución), `revisor` audita (solo lectura); también existen `backend-flask` y `disenador-vistas`. Ojo: esos `.md` dicen `insumos/` pero la carpeta real es `Insumo/`.
