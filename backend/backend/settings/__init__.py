import os


environment = os.getenv('DJANGO_ENVIRONMENT', 'local')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .production import *
    DEBUG = True
else:
    from .local import *