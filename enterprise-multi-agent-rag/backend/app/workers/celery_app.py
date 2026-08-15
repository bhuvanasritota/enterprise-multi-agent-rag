from celery import Celery
from app.core.config import settings
celery = Celery("enterpriserag", broker=settings.redis_url, backend=settings.redis_url, include=["app.workers.tasks"])
celery.conf.update(task_track_started=True, task_time_limit=1800, task_soft_time_limit=1700, task_acks_late=True, worker_prefetch_multiplier=1, task_always_eager=settings.celery_task_always_eager)
