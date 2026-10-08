"""Servicio de generación de certificados académicos en formato PDF.

Utiliza fpdf2 en formato A4 horizontal (297 mm x 210 mm) con paleta institucional
en azul marino (#14213D) y dorado (#B8923D).
Genera certificados individuales y paquetes comprimidos (.zip).
"""

import io
import re
import zipfile
from typing import Any, Dict, List
from fpdf import FPDF

# Paleta de colores institucional
COLOR_AZUL_MARINO = (20, 33, 61)    # #14213D
COLOR_DORADO = (184, 146, 61)       # #B8923D
COLOR_GRIS = (90, 100, 115)          # Texto secundario
COLOR_NEGRO = (33, 37, 41)


class CertificadoPDF(FPDF):
    """Clase personalizada para renderizar certificados en A4 horizontal."""

    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)

    def dibujar_marcos(self):
        """Dibuja marcos decorativos en azul marino y dorado."""
        # Marco exterior en azul marino
        self.set_draw_color(*COLOR_AZUL_MARINO)
        self.set_line_width(2.0)
        self.rect(8, 8, 281, 194)

        # Marco intermedio en dorado
        self.set_draw_color(*COLOR_DORADO)
        self.set_line_width(0.8)
        self.rect(12, 12, 273, 186)

        # Líneas decorativas en las esquinas interiores
        self.set_draw_color(*COLOR_DORADO)
        self.set_line_width(0.5)
        self.rect(14, 14, 269, 182)


def sanitizar_nombre_archivo(texto: str) -> str:
    """Convierte un texto en un nombre seguro para archivos."""
    limpio = re.sub(r"[^\w\s-]", "", texto).strip()
    return re.sub(r"[-\s]+", "_", limpio)


def generar_certificado_pdf(datos_estudiante: Dict[str, Any]) -> bytes:
    """Genera el certificado individual en formato PDF binario.
    
    Lanza ValueError si el estudiante no califica para certificado
    o presenta inconsistencias de datos.
    """
    tipo_certificado = datos_estudiante.get("tipo_certificado")
    tiene_inconsistencia = datos_estudiante.get("tiene_inconsistencia", False)

    if tiene_inconsistencia or tipo_certificado == "Sin certificado":
        raise ValueError(
            f"No es posible emitir certificado para {datos_estudiante.get('nombre_completo', 'el estudiante')}: "
            "cuenta con inconsistencias o estado 'Sin certificado'."
        )

    titulo_certificado = (
        "CERTIFICADO DE APROBACIÓN"
        if tipo_certificado == "Aprobación"
        else "CERTIFICADO DE PARTICIPACIÓN"
    )

    pdf = CertificadoPDF()
    pdf.add_page()
    pdf.dibujar_marcos()

    # 1. Encabezado institucional
    pdf.set_y(22)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*COLOR_DORADO)
    pdf.cell(0, 7, "ACADEMIA DE FORMACIÓN PROFESIONAL", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_GRIS)
    pdf.cell(0, 5, "SISTEMA OFICIAL DE CERTIFICACIÓN Y ACREDITACIÓN ACADÉMICA", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # 2. Título de la certificación
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*COLOR_AZUL_MARINO)
    pdf.cell(0, 10, titulo_certificado, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    # 3. Otorgado a
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(*COLOR_GRIS)
    pdf.cell(0, 6, "Se otorga el presente reconocimiento a:", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)

    # 4. Nombre del estudiante
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*COLOR_AZUL_MARINO)
    nombre = datos_estudiante.get("nombre_completo", "").upper()
    pdf.cell(0, 9, nombre, align="C", new_x="LMARGIN", new_y="NEXT")

    # Identificación
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COLOR_GRIS)
    ident = datos_estudiante.get("identificacion", "")
    pdf.cell(0, 6, f"Identificación: {ident}", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    # 5. Mérito del programa
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COLOR_NEGRO)
    texto_cumplimiento = (
        "Por haber completado y aprobado satisfactoriamente los módulos del programa:"
        if tipo_certificado == "Aprobación"
        else "Por su activa participación y asistencia en los módulos del programa:"
    )
    pdf.cell(0, 6, texto_cumplimiento, align="C", new_x="LMARGIN", new_y="NEXT")

    # Programa
    programa = datos_estudiante.get("programa", "")
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*COLOR_DORADO)
    pdf.cell(0, 7, programa, align="C", new_x="LMARGIN", new_y="NEXT")

    cohorte = datos_estudiante.get("cohorte", "")
    if cohorte:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*COLOR_GRIS)
        pdf.cell(0, 5, f"Cohorte: {cohorte}", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # 6. Cuadro de métricas académicas
    promedio = datos_estudiante.get("promedio", 0.0)
    asistencia = datos_estudiante.get("asistencia", 0.0)

    # Dibujar tarjeta de calificaciones centrada
    ancho_caja = 130
    alto_caja = 16
    x_caja = (297 - ancho_caja) / 2
    y_caja = pdf.get_y()

    pdf.set_draw_color(*COLOR_DORADO)
    pdf.set_fill_color(248, 249, 250)
    pdf.set_line_width(0.4)
    pdf.rect(x_caja, y_caja, ancho_caja, alto_caja, style="DF")

    pdf.set_xy(x_caja, y_caja + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*COLOR_AZUL_MARINO)
    pdf.cell(ancho_caja / 2, 5, "Promedio Final Obtenido", align="C")
    pdf.cell(ancho_caja / 2, 5, "Asistencia Registrada", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(x_caja)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_DORADO)
    pdf.cell(ancho_caja / 2, 6, f"{promedio:.2f} / 100", align="C")
    pdf.cell(ancho_caja / 2, 6, f"{asistencia:.2f} %", align="C", new_x="LMARGIN", new_y="NEXT")

    # 7. Firmas de validación
    pdf.set_y(168)
    ancho_firma = 70
    x_firma1 = 45
    x_firma2 = 182

    pdf.set_draw_color(*COLOR_AZUL_MARINO)
    pdf.set_line_width(0.5)
    pdf.line(x_firma1, 175, x_firma1 + ancho_firma, 175)
    pdf.line(x_firma2, 175, x_firma2 + ancho_firma, 175)

    pdf.set_xy(x_firma1, 177)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_AZUL_MARINO)
    pdf.cell(ancho_firma, 4, "DIRECCIÓN ACADÉMICA", align="C")

    pdf.set_xy(x_firma2, 177)
    pdf.cell(ancho_firma, 4, "SECRETARÍA GENERAL", align="C")

    pdf.set_xy(x_firma1, 181)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*COLOR_GRIS)
    pdf.cell(ancho_firma, 4, "Academia de Formación Profesional", align="C")

    pdf.set_xy(x_firma2, 181)
    pdf.cell(ancho_firma, 4, "Acreditación y Registros", align="C")

    return bytes(pdf.output())


def generar_zip_certificados(estudiantes: List[Dict[str, Any]]) -> io.BytesIO:
    """Genera un archivo comprimido .zip en memoria con todos los PDF emitibles.
    
    Filtra automáticamente estudiantes no certificables o con inconsistencias.
    """
    buffer_zip = io.BytesIO()

    with zipfile.ZipFile(buffer_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as archivo_zip:
        for est in estudiantes:
            # Excluir no certificables o inconsistencias
            if est.get("tiene_inconsistencia") or est.get("tipo_certificado") == "Sin certificado":
                continue

            try:
                contenido_pdf = generar_certificado_pdf(est)
                ident = est.get("identificacion", "id")
                nombre_slug = sanitizar_nombre_archivo(est.get("nombre_completo", "estudiante"))
                prog_slug = sanitizar_nombre_archivo(est.get("programa", "programa"))
                tipo_slug = sanitizar_nombre_archivo(est.get("tipo_certificado", "certificado"))

                nombre_archivo = f"{tipo_slug}_{ident}_{nombre_slug}_{prog_slug}.pdf"
                archivo_zip.writestr(nombre_archivo, contenido_pdf)
            except ValueError:
                continue

    buffer_zip.seek(0)
    return buffer_zip
