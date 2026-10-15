@echo off
REM Arranca la App de Certificados (Academia Horizonte) con doble clic.
REM Usa uv, que instala solo si falta algo. Para detener: Ctrl+C o cerrar esta ventana.
cd /d "%~dp0"
uv run python app.py
pause
