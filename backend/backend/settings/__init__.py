import os
import logging

logger = logging.getLogger(__name__)

environment = "local"


if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .production import *
    DEBUG = True
else:
    logger.info("local this is executed")
    from .local import *