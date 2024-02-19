import socket

from celery import Task
from celery.utils.log import get_task_logger
from django.db import OperationalError
from requests.exceptions import ConnectionError, Timeout

logger = get_task_logger(__name__)


class MyBaseTask(Task):
    # Define retry for common transient errors
    autoretry_for = (ConnectionError, Timeout, OperationalError, IOError, OSError, socket.error)
    retry_kwargs = {"max_retries": 3, "countdown": 15}

    # Default delay between retries, starting at x seconds and doubling each time
    # since retry_backoff is set to True
    retry_backoff = True
    default_retry_delay = 15
    # Acknowledge tasks only after they have been completed
    acks_late = True
    reject_on_worker_lost = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Custom handler for task failure."""
        logger.error(f"Task {self.name} [{task_id}] failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Custom handler for task retries."""
        logger.info(f"Task {self.name} [{task_id}] will be retried: {exc}")

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Handler called after the task is executed."""
        if status == "FAILURE":
            logger.error(f"Task {self.name} [{task_id}] failed.")
            pass
        else:
            logger.info(f"Task {self.name} [{task_id}] completed successfully.")
