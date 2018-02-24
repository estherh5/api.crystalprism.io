import os
import sys


sys.path.insert(0, '/var/www/html/api.crystalprism.io')  # Server path


def application(environ, start_response):
    os.environ['ENV_TYPE'] = environ.get('ENV_TYPE', '')
    os.environ['SECRET_KEY'] = environ.get('SECRET_KEY', '')
    os.environ['S3_BUCKET'] = environ.get('S3_BUCKET', '')
    os.environ['PHOTO_URL_START'] = environ.get('PHOTO_URL_START', '')
    os.environ['AWS_ACCESS_KEY_ID'] = environ.get('AWS_ACCESS_KEY_ID', '')
    os.environ['AWS_SECRET_ACCESS_KEY'] = environ.get(
        'AWS_SECRET_ACCESS_KEY', ''
        )
    from server import app as _application

    return _application(environ, start_response)
