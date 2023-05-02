from django.apps import AppConfig
from django.core.signals import request_finished

class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        from . import signals

        return super().ready()
