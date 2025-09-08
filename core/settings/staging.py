from .base import *
from decouple import config, Csv
import os

# Production-like settings
DEBUG = config("DEBUG", cast=bool, default=False)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", cast=Csv(), default="staging.adtech.com,*.run.app")

# CORS
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    cast=Csv(),
    default="https://staging-frontend.adtech.com"
)
CORS_ALLOW_CREDENTIALS = True

# DB (Cloud SQL MySQL - Staging instance)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),  # Cloud SQL staging instance
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# Redis (Memorystore - Staging instance)
REDIS_HOST = config("REDIS_HOST")
BROKER_DB = config("CELERY_BROKER_DB", cast=int, default=0)
RESULT_DB = config("CELERY_RESULT_DB", cast=int, default=1)
CACHE_DB = config("DJANGO_CACHE_DB", cast=int, default=2)

# Celery
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:6379/{BROKER_DB}"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:6379/{RESULT_DB}"

# Cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:6379/{CACHE_DB}",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "TIMEOUT": config("DJANGO_CACHE_TIMEOUT", cast=int, default=600),
    }
}

# Security
SECRET_KEY = config("SECRET_KEY")
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# GCP Logging
LOGGING = {
    'version': 1,
    'handlers': {
        'stackdriver': {
            'class': 'google.cloud.logging.handlers.CloudLoggingHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['stackdriver'],
            'level': 'WARNING',
        },
    },
}

# Staging specific - more restrictive
CELERY_TASK_TIME_LIMIT = config("CELERY_TASK_TIME_LIMIT", cast=int, default=1800)
CELERY_TASK_SOFT_TIME_LIMIT = config("CELERY_TASK_SOFT_TIME_LIMIT", cast=int, default=1500)