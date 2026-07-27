import os
from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
"subnet_ping_prj.settings"
)
app = Celery("subnet_app")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()