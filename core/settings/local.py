from .base import *  # noqa
from decouple import config, Csv

DEBUG = True
SECRET_KEY = config("SECRET_KEY", default="dev-only-not-secure")
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    cast=Csv(),
    default="http://localhost:5173,http://127.0.0.1:5173"
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="adtech_local"),
        "USER": config("DB_USER", default="root"),
        "PASSWORD": config("DB_PASSWORD", default="password"),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="3306"),
    }
}

REDIS_HOST = config("REDIS_HOST", default="127.0.0.1")
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:6379/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:6379/1"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:6379/2",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "TIMEOUT": 300,
    }
}
