"""Controlador para el tablero principal de certificaciones.

No ejecuta cálculos de negocio: delega completamente en models/certificados.py.
"""

from flask import Blueprint, render_template
from models.certificados import obtener_resumen_completo

tablero_bp = Blueprint("tablero", __name__)


@tablero_bp.route("/")
def index():
    """Ruta principal / que presenta el tablero general de certificados e inconsistencias."""
    datos_resumen = obtener_resumen_completo()
    return render_template(
        "tablero.html",
        contadores=datos_resumen["contadores"],
        inconsistencias=datos_resumen["inconsistencias"],
        estudiantes=datos_resumen["estudiantes"],
    )
