import os
import sys

sys.path.insert(0, '/var/www/html/canvashare') #server path

def application(environ, start_response):
    os.environ['ENV_TYPE'] = environ.get('ENV_TYPE', '')
    from canvashare import app as _application

    return _application(environ, start_response)
