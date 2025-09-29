import os
import logging

logger = logging.getLogger(__name__)

environment = os.getenv('DJANGO_ENVIRONMENT', 'local')
logger.info(f"This is env:  {environment}")

if environment == 'production':
    logger.info("production this is executed")
    from .production import *
elif environment == 'staging':
    logger.info("staging this is executed")
    from .production import *
    DEBUG = True
else:
    logger.info("local this is executed")
    from .local import *