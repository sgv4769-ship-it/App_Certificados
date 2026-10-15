"""Controlador para el tablero principal de certificaciones.

No ejecuta cálculos de negocio: delega completamente en models/certificados.py.
Recibe el filtro por programa (?programa=...) y lo aplica solo a la tabla;
los contadores siempre muestran el total general.
"""

from flask import Blueprint, render_template, request
from models.certificados import obtener_resumen_completo

tablero_bp = Blueprint("tablero", __name__)


@tablero_bp.route("/")
def index():
    """Ruta principal / que presenta el tablero general de certificados e inconsistencias."""
    datos_resumen = obtener_resumen_completo()
    estudiantes = datos_resumen["estudiantes"]

    # LADRILLO: variable que guarda el programa elegido en el filtro (texto).
    programa_sel = request.args.get("programa", "").strip()

    # LADRILLO: bucle que junta los programas existentes sin repetirlos, ordenados.
    programas = sorted({e["programa"] for e in estudiantes if e.get("programa")})

    # LADRILLO: condicional que filtra la tabla solo si se eligió un programa válido.
    if programa_sel in programas:
        estudiantes_vista = [e for e in estudiantes if e["programa"] == programa_sel]
    else:
        programa_sel = ""
        estudiantes_vista = estudiantes

    return render_template(
        "tablero.html",
        contadores=datos_resumen["contadores"],
        inconsistencias=datos_resumen["inconsistencias"],
        estudiantes=estudiantes_vista,
        programas=programas,
        programa_sel=programa_sel,
    )
