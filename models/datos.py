"""Capa de datos y acceso a la base de datos (PostgreSQL / Supabase y SQLite local).

Este módulo es el único punto de contacto con la base de datos.
Soporta:
1. Supabase (PostgreSQL) usando psycopg con prepare_threshold=None cuando DATABASE_URL está configurada.
2. SQLite local (certificados.db) como base de datos por defecto cuando aún no se ha configurado Supabase.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

DB_LOCAL_SQLITE = ROOT_DIR / "certificados.db"


def _es_postgres() -> bool:
    """Determina si se cuenta con una URL de PostgreSQL válida configurada."""
    url = os.environ.get("DATABASE_URL", "").strip()
    return url.startswith("postgresql://") or url.startswith("postgres://")


@contextmanager
def obtener_conexion():
    """Generador de contexto para la conexión a la base de datos activa.
    
    Si DATABASE_URL está configurada para PostgreSQL, conecta con psycopg (prepare_threshold=None).
    Si no, conecta a SQLite local en certificados.db con filas en formato diccionario.
    """
    if _es_postgres():
        import psycopg
        from psycopg.rows import dict_row

        database_url = os.environ.get("DATABASE_URL")
        conn = psycopg.connect(
            database_url,
            prepare_threshold=None,
            row_factory=dict_row
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(DB_LOCAL_SQLITE)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def crear_tablas() -> None:
    """Crea las tablas 'estudiantes' y 'evaluaciones' si no existen."""
    es_pg = _es_postgres()

    pk_eval = "SERIAL PRIMARY KEY" if es_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"

    ddl_estudiantes = """
    CREATE TABLE IF NOT EXISTS estudiantes (
        identificacion TEXT PRIMARY KEY,
        nombre_completo TEXT NOT NULL,
        correo TEXT,
        programa TEXT,
        cohorte TEXT
    );
    """

    ddl_evaluaciones = f"""
    CREATE TABLE IF NOT EXISTS evaluaciones (
        id {pk_eval},
        identificacion TEXT NOT NULL,
        programa TEXT NOT NULL,
        modulo TEXT NOT NULL,
        nota NUMERIC(5, 2) NOT NULL,
        asistencia_pct NUMERIC(5, 2) NOT NULL,
        fecha_cierre DATE
    );
    """

    ddl_indices = """
    CREATE INDEX IF NOT EXISTS idx_evaluaciones_ident_prog 
    ON evaluaciones (identificacion, programa);
    """

    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute(ddl_estudiantes)
        cur.execute(ddl_evaluaciones)
        cur.execute(ddl_indices)
        cur.close()


def guardar_estudiantes(estudiantes: List[Dict[str, Any]]) -> int:
    """Inserta o actualiza un lote de estudiantes en la base de datos (upsert)."""
    if not estudiantes:
        return 0

    es_pg = _es_postgres()

    if es_pg:
        query = """
        INSERT INTO estudiantes (identificacion, nombre_completo, correo, programa, cohorte)
        VALUES (%(identificacion)s, %(nombre_completo)s, %(correo)s, %(programa)s, %(cohorte)s)
        ON CONFLICT (identificacion) DO UPDATE SET
            nombre_completo = EXCLUDED.nombre_completo,
            correo = EXCLUDED.correo,
            programa = EXCLUDED.programa,
            cohorte = EXCLUDED.cohorte;
        """
    else:
        query = """
        INSERT INTO estudiantes (identificacion, nombre_completo, correo, programa, cohorte)
        VALUES (:identificacion, :nombre_completo, :correo, :programa, :cohorte)
        ON CONFLICT (identificacion) DO UPDATE SET
            nombre_completo = excluded.nombre_completo,
            correo = excluded.correo,
            programa = excluded.programa,
            cohorte = excluded.cohorte;
        """

    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.executemany(query, estudiantes)
        cur.close()
        return len(estudiantes)


def guardar_evaluaciones(evaluaciones: List[Dict[str, Any]], limpiar_existentes: bool = True) -> int:
    """Inserta un lote de evaluaciones en la base de datos."""
    if not evaluaciones and not limpiar_existentes:
        return 0

    es_pg = _es_postgres()

    with obtener_conexion() as conn:
        cur = conn.cursor()
        if limpiar_existentes:
            if es_pg:
                cur.execute("TRUNCATE TABLE evaluaciones RESTART IDENTITY;")
            else:
                cur.execute("DELETE FROM evaluaciones;")
                cur.execute("DELETE FROM sqlite_sequence WHERE name = 'evaluaciones';")

        if evaluaciones:
            # Formatear fechas a string ISO si es SQLite
            evaluaciones_formateadas = []
            for ev in evaluaciones:
                ev_copia = dict(ev)
                if not es_pg and ev_copia.get("fecha_cierre") is not None:
                    ev_copia["fecha_cierre"] = str(ev_copia["fecha_cierre"])
                evaluaciones_formateadas.append(ev_copia)

            if es_pg:
                query = """
                INSERT INTO evaluaciones (identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre)
                VALUES (%(identificacion)s, %(programa)s, %(modulo)s, %(nota)s, %(asistencia_pct)s, %(fecha_cierre)s);
                """
            else:
                query = """
                INSERT INTO evaluaciones (identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre)
                VALUES (:identificacion, :programa, :modulo, :nota, :asistencia_pct, :fecha_cierre);
                """
            cur.executemany(query, evaluaciones_formateadas)
        cur.close()
        return len(evaluaciones)


def obtener_todos_estudiantes() -> List[Dict[str, Any]]:
    """Recupera todos los registros de la tabla estudiantes."""
    query = """
    SELECT identificacion, nombre_completo, correo, programa, cohorte
    FROM estudiantes
    ORDER BY nombre_completo ASC;
    """
    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute(query)
        filas = cur.fetchall()
        cur.close()
        return [dict(f) for f in filas]


def obtener_todas_evaluaciones() -> List[Dict[str, Any]]:
    """Recupera todos los registros de la tabla evaluaciones."""
    query = """
    SELECT id, identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre
    FROM evaluaciones
    ORDER BY identificacion ASC, modulo ASC;
    """
    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute(query)
        filas = cur.fetchall()
        cur.close()
        return [dict(f) for f in filas]


def contar_registros() -> Dict[str, int]:
    """Retorna el conteo actual de registros en las tablas de la base de datos."""
    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM estudiantes;")
        total_estudiantes = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM evaluaciones;")
        total_evaluaciones = cur.fetchone()["total"]
        cur.close()
        return {
            "estudiantes": total_estudiantes,
            "evaluaciones": total_evaluaciones,
        }
