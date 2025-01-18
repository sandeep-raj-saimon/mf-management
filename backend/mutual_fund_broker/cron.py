from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mutual_fund_broker.settings')

app = Celery('mutual_fund_broker')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Periodic tasks schedule
app.conf.beat_schedule = {
    'update-nav-at-midnight': {
        'task': 'brokerService.tasks.update_or_create_nav',  # Example: Update this to your actual task path
        'schedule': crontab(hour=0, minute=0),
    },
    'fetch-fund-families-at-1230am': {
        'task': 'brokerService.tasks.fetch_fund_families',  # Example: Update this to your actual task path
        'schedule': crontab(hour=0, minute=30),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
