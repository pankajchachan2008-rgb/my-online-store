import os
from celery import Celery

# Django की सेटिंग्स को Celery के लिए डिफ़ॉल्ट सेट करें
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store_backend.settings')

app = Celery('store_backend')

# namespace='CELERY' का मतलब है कि celery की सेटिंग्स CELERY_ से शुरू होंगी
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django के सभी ऐप्स में tasks.py को खुद ढूँढ लेगा
app.autodiscover_tasks()