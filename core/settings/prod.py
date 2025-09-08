from .base import *
from decouple import config, Csv
import os

# Production settings
DEBUG = False
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", cast=Csv(), default="api.adtech.com,adtech.com,*.run.app")

# CORS - Restrictivo
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    cast=Csv(),
    default="https://app.adtech.com,https://dashboard.adtech.com"
)
CORS_ALLOW_CREDENTIALS = True

# DB (Cloud SQL MySQL - Production HA)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),  # Cloud SQL HA instance
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "sql_mode": "STRICT_TRANS_TABLES",
        },
        "CONN_MAX_AGE": 600,  # Connection pooling
    }
}

# Redis (Memorystore - Production HA)
REDIS_HOST = config("REDIS_HOST")
BROKER_DB = config("CELERY_BROKER_DB", cast=int, default=0)
RESULT_DB = config("CELERY_RESULT_DB", cast=int, default=1)
CACHE_DB = config("DJANGO_CACHE_DB", cast=int, default=2)

# Celery - Production optimized
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:6379/{BROKER_DB}"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:6379/{RESULT_DB}"
CELERY_TASK_TIME_LIMIT = config("CELERY_TASK_TIME_LIMIT", cast=int, default=3600)
CELERY_TASK_SOFT_TIME_LIMIT = config("CELERY_TASK_SOFT_TIME_LIMIT", cast=int, default=3300)
CELERY_WORKER_CONCURRENCY = config("CELERY_WORKER_CONCURRENCY", cast=int, default=4)

# Cache - Production optimized
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:6379/{CACHE_DB}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50}
        },
        "TIMEOUT": config("DJANGO_CACHE_TIMEOUT", cast=int, default=3600),
    }
}

# Security - Production hardened
SECRET_KEY = config("SECRET_KEY")
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# GCP Production Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'stackdriver': {
            'class': 'google.cloud.logging.handlers.CloudLoggingHandler',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['stackdriver'],
            'level': 'ERROR',
            'propagate': False,
        },
        'celery': {
            'handlers': ['stackdriver'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Static files (Cloud Storage)
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = config("GS_BUCKET_NAME")
STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"