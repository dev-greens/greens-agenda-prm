from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def heartbeat():
    logger.info("heartbeat ok")
    return True
