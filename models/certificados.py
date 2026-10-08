"""Módulo de reglas de negocio para la emisión y clasificación de certificados.

Aloja de forma exclusiva las constantes y la lógica del negocio:
- Constantes: NOTA_MINIMA = 70, ASISTENCIA_MINIMA = 80, ASISTENCIA_CRITICA = 50.
- Reglas R1 a R6.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from models.datos import obtener_todos_estudiantes, obtener_todas_evaluaciones

# Constantes del negocio (Inviolables según AGENTS.md)
NOTA_MINIMA: float = 70.0
ASISTENCIA_MINIMA: float = 80.0
ASISTENCIA_CRITICA: float = 50.0

ESTADO_APROBACION: str = "Aprobación"
ESTADO_PARTICIPACION: str = "Participación"
ESTADO_SIN_CERTIFICADO: str = "Sin certificado"


def clasificar_certificado(promedio: float, asistencia: float) -> str:
    """Aplica las reglas R3, R4 y R5 para clasificar el estado de certificación.
    
    - R5. Sin certificado: asistencia < 80.
    - R3. Aprobación: promedio >= 70 y asistencia >= 80 (límites inclusive).
    - R4. Participación: promedio < 70 y asistencia >= 80.
    """
    if asistencia < ASISTENCIA_MINIMA:
        return ESTADO_SIN_CERTIFICADO
    if promedio >= NOTA_MINIMA:
        return ESTADO_APROBACION
    return ESTADO_PARTICIPACION


def obtener_resumen_completo() -> Dict[str, Any]:
    """Procesa estudiantes y evaluaciones aplicando las reglas R1 a R6.
    
    Retorna un diccionario con:
    - contadores: conteos exactos de Aprobación, Participación y Sin certificado.
    - inconsistencias: lista de alertas estructuradas según R6.
    - estudiantes_certificados: lista detallada para la tabla de la interfaz.
    """
    estudiantes = obtener_todos_estudiantes()
    evaluaciones = obtener_todas_evaluaciones()

    maestro_por_id: Dict[str, Dict[str, Any]] = {
        e["identificacion"]: e for e in estudiantes
    }

    # R1: Agrupar evaluaciones por (identificacion, programa)
    grupos_evaluaciones: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for evaluacion in evaluaciones:
        llave = (evaluacion["identificacion"], evaluacion["programa"])
        grupos_evaluaciones[llave].append(evaluacion)

    inconsistencias: List[Dict[str, Any]] = []
    estudiantes_certificados: List[Dict[str, Any]] = []

    conteo_aprobacion = 0
    conteo_participacion = 0
    conteo_sin_certificado = 0

    ids_con_evaluaciones = set()

    # Procesar cada grupo de evaluaciones
    for (identificacion, programa), lista_evals in sorted(grupos_evaluaciones.items()):
        ids_con_evaluaciones.add(identificacion)

        # R2: Promedio de notas y promedio de asistencia, redondeados a 2 decimales
        notas = [float(ev["nota"]) for ev in lista_evals]
        asistencias = [float(ev["asistencia_pct"]) for ev in lista_evals]

        promedio = round(sum(notas) / len(notas), 2) if notas else 0.0
        asistencia = round(sum(asistencias) / len(asistencias), 2) if asistencias else 0.0

        # R6 Caso B: Identificación con evaluaciones que no está en el maestro
        if identificacion not in maestro_por_id:
            inconsistencias.append({
                "identificacion": identificacion,
                "nombre_completo": "No registrado en Maestro",
                "programa": programa,
                "promedio": promedio,
                "asistencia": asistencia,
                "tipo": "Identificación sin registro en maestro",
                "descripcion": f"La identificación {identificacion} posee evaluaciones en '{programa}' pero no existe en el Maestro de Estudiantes.",
            })
            continue

        estudiante = maestro_por_id[identificacion]
        nombre_completo = estudiante["nombre_completo"]
        correo = estudiante.get("correo", "")
        cohorte = estudiante.get("cohorte", "")

        # R6 Caso C: Asistencia menor al 50 %
        es_asistencia_critica = asistencia < ASISTENCIA_CRITICA
        if es_asistencia_critica:
            inconsistencias.append({
                "identificacion": identificacion,
                "nombre_completo": nombre_completo,
                "programa": programa,
                "promedio": promedio,
                "asistencia": asistencia,
                "tipo": "Asistencia crítica (< 50 %)",
                "descripcion": f"{nombre_completo} ({identificacion}) registra una asistencia promedio de {asistencia}%, inferior al umbral crítico del 50%.",
            })

        # Clasificación de certificados (R3, R4, R5)
        tipo_cert = clasificar_certificado(promedio, asistencia)

        if tipo_cert == ESTADO_APROBACION:
            conteo_aprobacion += 1
        elif tipo_cert == ESTADO_PARTICIPACION:
            conteo_participacion += 1
        else:
            conteo_sin_certificado += 1

        estudiantes_certificados.append({
            "identificacion": identificacion,
            "nombre_completo": nombre_completo,
            "correo": correo,
            "programa": programa,
            "cohorte": cohorte,
            "promedio": promedio,
            "asistencia": asistencia,
            "tipo_certificado": tipo_cert,
            "tiene_inconsistencia": es_asistencia_critica,
            "puede_descargar": not es_asistencia_critica and tipo_cert != ESTADO_SIN_CERTIFICADO,
        })

    # R6 Caso A: Estudiante del maestro sin evaluaciones
    for identificacion, estudiante in sorted(maestro_por_id.items(), key=lambda item: item[1]["nombre_completo"]):
        if identificacion not in ids_con_evaluaciones:
            inconsistencias.append({
                "identificacion": identificacion,
                "nombre_completo": estudiante["nombre_completo"],
                "programa": estudiante.get("programa", "No asignado"),
                "promedio": None,
                "asistencia": None,
                "tipo": "Estudiante sin evaluaciones",
                "descripcion": f"{estudiante['nombre_completo']} ({identificacion}) está registrado en el Maestro pero no registra evaluaciones en el sistema.",
            })

    # Ordenar lista de certificados por nombre completo para visualización limpia
    estudiantes_certificados.sort(key=lambda x: x["nombre_completo"])

    return {
        "contadores": {
            "aprobacion": conteo_aprobacion,
            "participacion": conteo_participacion,
            "sin_certificado": conteo_sin_certificado,
            "total_inconsistencias": len(inconsistencias),
        },
        "inconsistencias": inconsistencias,
        "estudiantes": estudiantes_certificados,
    }
