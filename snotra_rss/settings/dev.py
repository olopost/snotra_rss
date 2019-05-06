from .base import *

# SECURITY WARNING: don't run with debug turned on in production!

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*olp&eafu%bws-r#8w-u0)$%_q$(1+*!ar^z5uii#&-+njkm62'

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*'] 

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEBUG = False
DATADOG_LOG = False
DATADOG_API = 'd1fb27427cf53ce5bbac4bd3df5fcb09'
DATADOG_HOST = 'intake.logs.datadoghq.com'
DATADOG_PORT = 10514
OVH_LOG = True
OVH_TOKEN = "f37abc7f-b8b7-4c4c-aa34-ce7b80a2883a"
OVH_URL = 'gra2.logs.ovh.com'
OVH_PORT = 2202

if DATADOG_LOG:
    from datadog import initialize

    options = {
        'api_key':'790cdf015749d2d7aee225767ab226d6',
        'app_key':'aaa251ff3cf249af828b87d33717fc528544a03c'
    }

    initialize(**options)

try:
    from .local import *
except ImportError:
    pass
