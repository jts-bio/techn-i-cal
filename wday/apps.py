from django.apps import AppConfig


class WdayConfig(AppConfig):
    default_auto_field  = 'django.db.models.BigAutoField'
    name                = 'wday'
    verbose_name        = 'Workday'
    
class WTagsConfig(AppConfig):
    default_auto_field  = 'django.db.models.BigAutoField'
    name                = 'wday.templatetags.wtags'
    verbose_name        = 'Workday Tags'