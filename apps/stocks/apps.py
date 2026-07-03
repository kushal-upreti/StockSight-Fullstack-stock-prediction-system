import os
from django.apps import AppConfig


class StocksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stocks"

    def ready(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("ready() called — RUN_MAIN=%r, PID=%s", os.environ.get("RUN_MAIN"), os.getpid())
    
        if os.environ.get("RUN_MAIN") != "true":
            return
        from .scheduler import start_scheduler
        start_scheduler()