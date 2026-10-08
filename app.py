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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
