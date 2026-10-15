"""Servicio de carga y procesamiento de archivos Excel.

Lee los archivos Maestro_Estudiantes.xlsx y Registro_Evaluaciones.xlsx,
aplica las transformaciones y validaciones estructurales de tipos,
y delega el guardado estructurado en models/datos.py.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Asegurar que la raíz del proyecto esté en sys.path para ejecución directa del script
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from models.datos import (
    crear_tablas,
    guardar_estudiantes,
    guardar_evaluaciones,
    contar_registros,
)


def _resolver_ruta_insumo(nombre_archivo: str, ruta_provista: Optional[Union[str, Path]] = None) -> Path:
    """Resuelve la ruta física del archivo de entrada soportando nombres de carpeta comunes."""
    if ruta_provista:
        ruta = Path(ruta_provista)
        if ruta.exists():
            return ruta
        raise FileNotFoundError(f"No se encontró el archivo especificado: {ruta_provista}")

    # Rutas ancladas a la raíz del proyecto (donde vive este archivo),
    # para que funcionen sin importar desde dónde se ejecute la app.
    directorios_candidatos = ["insumos", "Insumo", "Insumos"]
    for dir_nombre in directorios_candidatos:
        candidato = ROOT_DIR / dir_nombre / nombre_archivo
        if candidato.exists():
            return candidato

    # Fallback default
    return ROOT_DIR / "insumos" / nombre_archivo


def leer_maestro_estudiantes(ruta_archivo: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Lee y limpia la hoja 'Estudiantes' del archivo de Maestro de Estudiantes.
    
    Retorna una lista de diccionarios con las llaves requeridas para la base de datos.
    """
    ruta_real = _resolver_ruta_insumo("Maestro_Estudiantes.xlsx", ruta_archivo)
    df = pd.read_excel(ruta_real, sheet_name="Estudiantes", dtype={"Identificacion": str})

    columnas_esperadas = ["Identificacion", "Nombre_Completo", "Correo", "Programa", "Cohorte"]
    for col in columnas_esperadas:
        if col not in df.columns:
            raise ValueError(f"Falta la columna requerida '{col}' en la hoja Estudiantes.")

    estudiantes: List[Dict[str, Any]] = []
    for _, fila in df.iterrows():
        identificacion_raw = fila.get("Identificacion")
        if pd.isna(identificacion_raw):
            continue

        identificacion = str(identificacion_raw).strip()
        if identificacion.endswith(".0"):
            identificacion = identificacion[:-2]

        nombre_completo = str(fila.get("Nombre_Completo", "")).strip() if pd.notna(fila.get("Nombre_Completo")) else ""
        correo = str(fila.get("Correo", "")).strip() if pd.notna(fila.get("Correo")) else ""
        programa = str(fila.get("Programa", "")).strip() if pd.notna(fila.get("Programa")) else ""
        cohorte = str(fila.get("Cohorte", "")).strip() if pd.notna(fila.get("Cohorte")) else ""

        estudiantes.append({
            "identificacion": identificacion,
            "nombre_completo": nombre_completo,
            "correo": correo,
            "programa": programa,
            "cohorte": cohorte,
        })

    return estudiantes


def leer_registro_evaluaciones(ruta_archivo: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Lee y limpia la hoja 'Evaluaciones' del archivo de Registro de Evaluaciones.
    
    Retorna una lista de diccionarios con las llaves requeridas para la base de datos.
    """
    ruta_real = _resolver_ruta_insumo("Registro_Evaluaciones.xlsx", ruta_archivo)
    df = pd.read_excel(ruta_real, sheet_name="Evaluaciones", dtype={"Identificacion": str})

    columnas_esperadas = ["Identificacion", "Programa", "Modulo", "Nota", "Asistencia_Pct", "Fecha_Cierre"]
    for col in columnas_esperadas:
        if col not in df.columns:
            raise ValueError(f"Falta la columna requerida '{col}' en la hoja Evaluaciones.")

    evaluaciones: List[Dict[str, Any]] = []
    for _, fila in df.iterrows():
        identificacion_raw = fila.get("Identificacion")
        if pd.isna(identificacion_raw):
            continue

        identificacion = str(identificacion_raw).strip()
        if identificacion.endswith(".0"):
            identificacion = identificacion[:-2]

        programa = str(fila.get("Programa", "")).strip() if pd.notna(fila.get("Programa")) else ""
        modulo = str(fila.get("Modulo", "")).strip() if pd.notna(fila.get("Modulo")) else ""

        try:
            nota = float(fila.get("Nota", 0.0))
        except (ValueError, TypeError):
            nota = 0.0

        try:
            asistencia_pct = float(fila.get("Asistencia_Pct", 0.0))
        except (ValueError, TypeError):
            asistencia_pct = 0.0

        fecha_raw = fila.get("Fecha_Cierre")
        fecha_cierre = None
        if pd.notna(fecha_raw):
            try:
                fecha_dt = pd.to_datetime(fecha_raw)
                fecha_cierre = fecha_dt.date()
            except Exception:
                fecha_cierre = None

        evaluaciones.append({
            "identificacion": identificacion,
            "programa": programa,
            "modulo": modulo,
            "nota": round(nota, 2),
            "asistencia_pct": round(asistencia_pct, 2),
            "fecha_cierre": fecha_cierre,
        })

    return evaluaciones


def procesar_y_cargar_excel(
    ruta_maestro: Optional[Union[str, Path]] = None,
    ruta_evaluaciones: Optional[Union[str, Path]] = None,
) -> Dict[str, int]:
    """Orquesta la lectura de ambos Excel, la creación de tablas y el guardado en Supabase."""
    # 1. Asegurar la creación de tablas en Supabase
    crear_tablas()

    # 2. Leer datos desde los archivos Excel
    estudiantes = leer_maestro_estudiantes(ruta_maestro)
    evaluaciones = leer_registro_evaluaciones(ruta_evaluaciones)

    # 3. Guardar en base de datos mediante el modelo
    total_estudiantes = guardar_estudiantes(estudiantes)
    total_evaluaciones = guardar_evaluaciones(evaluaciones, limpiar_existentes=True)

    # 4. Validar conteos
    conteo_bd = contar_registros()

    return {
        "estudiantes_leidos": len(estudiantes),
        "estudiantes_guardados": total_estudiantes,
        "estudiantes_en_bd": conteo_bd["estudiantes"],
        "evaluaciones_leidas": len(evaluaciones),
        "evaluaciones_guardadas": total_evaluaciones,
        "evaluaciones_en_bd": conteo_bd["evaluaciones"],
    }


if __name__ == "__main__":
    print("Iniciando proceso de carga de datos a la base de datos...")
    try:
        resultado = procesar_y_cargar_excel()
        print("Proceso completado con exito:")
        print(f" - Estudiantes procesados: {resultado['estudiantes_guardadas' if 'estudiantes_guardadas' in resultado else 'estudiantes_guardados']} (Total en BD: {resultado['estudiantes_en_bd']})")
        print(f" - Evaluaciones procesadas: {resultado['evaluaciones_guardadas']} (Total en BD: {resultado['evaluaciones_en_bd']})")
    except Exception as error:
        print(f"Error durante la carga de datos: {error}")
        raise
