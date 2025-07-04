import os
from django.conf import settings
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_conf.settings')

app = Celery('main_conf')
app.config_from_object('django.conf:settings')

app.autodiscover_tasks()


app.conf.timezone = settings.TIME_ZONE
app.conf.update(result_extended=True)
