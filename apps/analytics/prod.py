from .base import *

DEBUG = False
ALLOWED_HOSTS = ['api.adtech.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'adtech_prod',
        'USER': 'prod_user',
        'PASSWORD': 'prod_password',
        'HOST': 'prod-mysql.gcp.com',
        'PORT': '3306',
    }
}