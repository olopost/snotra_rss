from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'fp(3w=ugr60jtkhc)6yo+=nx5naev%&grc&1s!r=1+^3gqax8g'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'blog',
        'USER': 'blog',
        'PASSWORD': '5sdmpia',
        'HOST': 'db',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
    }
}
