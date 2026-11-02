"""Object storage: the `crystalprism` Cloudflare R2 bucket, through boto3's
S3 API.

Homepage photos live under PHOTO_DIR and CanvaShare drawings under
DRAWING_DIR. Objects are served publicly from R2_PUBLIC_BASE (the bucket's
r2.dev URL), and that public URL is what gets stored in drawing.url.
"""
import boto3
import os

PHOTO_DIR = 'photos/'
DRAWING_DIR = 'canvashare/'


def bucket():
    s3 = boto3.resource(
        's3',
        endpoint_url='https://' + os.environ['R2_ACCOUNT_ID'] +
            '.r2.cloudflarestorage.com',
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        region_name='auto'
        )
    return s3.Bucket(os.environ['R2_BUCKET'])


def public_url(key):
    return os.environ['R2_PUBLIC_BASE'].rstrip('/') + '/' + key
