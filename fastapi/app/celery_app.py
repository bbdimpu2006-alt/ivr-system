import os
from celery import Celery

REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'redis_pass')
REDIS_URL = os.getenv('REDIS_URL', f'redis://:{REDIS_PASSWORD}@redis:6379/0')

celery_app = Celery(
    'ivr',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
)
