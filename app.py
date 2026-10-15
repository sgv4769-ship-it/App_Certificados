"""Punto de entrada de la aplicación Flask.

Inicializa la aplicación en la variable `app`, configura la carpeta de plantillas
en 'views' respetando la arquitectura MVC, registra los controladores
y ejecuta el servidor web en el puerto 5000.
"""

from flask import Flask
from controllers.tablero import tablero_bp
from controllers.certificados import certificados_bp

app = Flask(__name__, template_folder="views", static_folder="views/static")

# Registro de controladores (Blueprints)
app.register_blueprint(tablero_bp)
app.register_blueprint(certificados_bp)


def inicializar_bd() -> None:
    """Prepara la base de datos al arrancar (clave en Vercel, donde no hay BD previa).

    Crea las tablas y, si están vacías y existen los Excel en Insumo/,
    los carga. Localmente no cambia nada porque la BD ya tiene datos.
    Nunca tumba el arranque: si algo falla, la página mostrará vacíos.
    """
    try:
        from models.datos import crear_tablas, contar_registros

        crear_tablas()
        conteo = contar_registros()
        if conteo["estudiantes"] == 0 and conteo["evaluaciones"] == 0:
            from services.carga_excel import procesar_y_cargar_excel

            procesar_y_cargar_excel()
    except Exception as error:
        print(f"Aviso: no se pudo inicializar la BD: {error}")


inicializar_bd()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
