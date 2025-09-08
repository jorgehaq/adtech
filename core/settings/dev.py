from .base import *
from decouple import config

DEBUG = config('DEBUG', default=True, cast=bool)

# Permite los hosts desde la variable de entorno y los hosts de desarrollo fijos.
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='').split(',') + ['localhost', '127.0.0.1', 'dev.adtech.com']

# CORS configuration for local development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    'http://192.168.163.150'
]

CORS_ALLOW_CREDENTIALS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'adtech_local',
        'USER': 'root',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

CELERY_BROKER_URL = 'redis://localhost:6379'