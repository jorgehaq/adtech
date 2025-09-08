from .base import *
from decouple import config, Csv
import os

# DEBUG y hosts  
DEBUG = config("DEBUG", cast=bool, default=False)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", cast=Csv(), default="dev.adtech.com,*.run.app")

# CORS
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    cast=Csv(),
    default="https://dev-frontend.adtech.com"
)
CORS_ALLOW_CREDENTIALS = True

# DB (Cloud SQL MySQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"), 
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),  # Cloud SQL private IP
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# Redis (Memorystore)
REDIS_HOST = config("REDIS_HOST")  # Memorystore private IP
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
        "TIMEOUT": config("DJANGO_CACHE_TIMEOUT", cast=int, default=300),
    }
}

# GCP specific
SECRET_KEY = config("SECRET_KEY")
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
            'level': 'INFO',
        },
    },
}