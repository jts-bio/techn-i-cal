from django.apps import AppConfig


class SchConfig(AppConfig):
    default_auto_field  = "django.db.models.BigAutoField"
    name                = "sch"
    verbose_name        = "Scheduler"

class TagsConfig(AppConfig):
    default_auto_field  = 'django.db.models.BigAutoField'
    name                = 'sch.templatetags.tags'
