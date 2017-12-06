import os
import sys

sys.path.insert(0, '/var/www/html/api.crystalprism.io') #server path

def application(environ, start_response):
    os.environ['ENV_TYPE'] = environ.get('ENV_TYPE', '')
    os.environ['SECRET_KEY'] = environ.get('SECRET_KEY', '')
    from . import app as _application

    return _application(environ, start_response)
