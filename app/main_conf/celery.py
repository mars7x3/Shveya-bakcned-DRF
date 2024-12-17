import os
from django.conf import settings
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_conf.settings')

app = Celery('main_conf')
app.config_from_object('django.conf:settings')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'task_change_product_cost_price': {
        'task': 'tasks.product.change_product_cost_price',
        'schedule': crontab(hour=6, minute=0),
    },

}

app.conf.timezone = settings.TIME_ZONE
app.conf.update(result_extended=True)
