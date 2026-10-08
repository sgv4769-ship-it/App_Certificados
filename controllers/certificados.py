"""Controlador para la emisión y descarga de certificados en PDF y archivo ZIP.

Delega la lógica en models/certificados.py y services/generador_pdf.py.
"""

import io
from flask import Blueprint, abort, send_file
from models.certificados import obtener_resumen_completo
from services.generador_pdf import generar_certificado_pdf, generar_zip_certificados

certificados_bp = Blueprint("certificados", __name__)


@certificados_bp.route("/certificado/<identificacion>/<path:programa>")
def ver_certificado(identificacion: str, programa: str):
    """Genera y muestra en el navegador el PDF del certificado para un estudiante y programa."""
    resumen = obtener_resumen_completo()
    estudiantes = resumen["estudiantes"]

    # Buscar coincidencia exacta por identificación y programa
    estudiante = next(
        (
            e for e in estudiantes
            if e["identificacion"] == identificacion.strip()
            and e["programa"].lower() == programa.strip().lower()
        ),
        None
    )

    if not estudiante:
        abort(404, description="No se encontró registro de certificación para los datos solicitados.")

    if not estudiante.get("puede_descargar"):
        abort(
            400,
            description="El estudiante no califica para emisión de certificado debido a estado 'Sin certificado' o inconsistencias detectadas."
        )

    try:
        pdf_bytes = generar_certificado_pdf(estudiante)
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)
        nombre_descarga = f"Certificado_{estudiante['identificacion']}.pdf"

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=nombre_descarga,
        )
    except ValueError as e:
        abort(400, description=str(e))


@certificados_bp.route("/descargar-todos")
def descargar_todos():
    """Genera y descarga un archivo .zip conteniendo todos los certificados emitibles."""
    resumen = obtener_resumen_completo()
    estudiantes = resumen["estudiantes"]

    zip_buffer = generar_zip_certificados(estudiantes)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="certificados.zip",
    )
