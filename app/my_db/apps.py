from django.apps import AppConfig


class MyDbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_db'
