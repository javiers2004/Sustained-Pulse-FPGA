from __future__ import unicode_literals, print_function, division
import time
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_redis import FlaskRedis
from weblablib import WebLab
from config import config

weblab = WebLab()
toolbar = DebugToolbarExtension()
redis = FlaskRedis(decode_responses=True)

def create_app(config_name):
    """
    This is a factory method. You can provide different setting names
    (development, testing, production) and it will initialize a Flask
    app with those settings. Check 'config.py' for further information.
    """
    app = Flask(__name__)
    config_class = config[config_name]
    print("{}: Using config: {}".format(time.asctime(), config_class.__name__))
    app.config.from_object(config_class)

    app.config.update# __init__.py

from __future__ import unicode_literals, print_function, division
import time
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_redis import FlaskRedis
from weblablib import WebLab
from config import config

weblab = WebLab()
toolbar = DebugToolbarExtension()
redis = FlaskRedis(decode_responses=True)

def create_app(config_name):
    """
    Esta es una función de fábrica para crear la instancia de la aplicación Flask.
    Se configura la aplicación dependiendo del entorno (desarrollo, producción, etc.).
    """
    app = Flask(__name__)
    config_class = config[config_name]  # Configuración basada en el entorno
    print("{}: Using config: {}".format(time.asctime(), config_class.__name__))
    app.config.from_object(config_class)

    # Actualización de algunas configuraciones de la aplicación
    app.config.update({
        'SECRET_KEY': '\x18\xf2\xb0\x8d\x02\xef\xef\xf7@&H\xad\xb6\x91O\t,Y\xd4\\i\x15L)\x92\x8f\x14\x82\x86\xd5=&',
        'WEBLAB_USERNAME': 'weblabdeusto',
        'WEBLAB_PASSWORD': 'password',
    })

    # Inicializar las extensiones de Flask
    weblab.init_app(app)
    toolbar.init_app(app)
    redis.init_app(app)

    # Registrar las vistas
    from .labController import main_blueprint
    app.register_blueprint(main_blueprint)

    # Registrar la limpieza de recursos
    from .labHardware import clean_resources

    @app.cli.command('clean-resources')
    def clean_resources_command():
        """
        Comando para limpiar recursos a través de Flask CLI.
        """
        clean_resources()

    # La app ahora está configurada y lista
    return app
: 'weblabdeusto',
    'WEBLAB_PASSWORD': 'password',
})

    # Initialize the Flask plug-ins (including WebLab)
    weblab.init_app(app)
    toolbar.init_app(app)
    redis.init_app(app)

    # Register the views
    from .views import main_blueprint
    app.register_blueprint(main_blueprint)

    from .hardware import clean_resources

    @app.cli.command('clean-resources')
    def clean_resources_command():
        """
        You can now run:
        $ flask clean-resources

        And it will call the clean_resources method. Imagine that you have a 
        resource which is telling a motor to move against a wall, and suddenly 
        the computer where this code runs is restarted (due to an external 
        factor). You want that the server, as soon as it starts, stops that 
        procedure.

        Doing this, in the launching script you can call "flask clean-resoures" 
        so every time you run the lab, first it stops any ongoing action.
        """
        clean_resources()

    # app is a valid Flask app
    return app

