from __future__ import annotations

from celery import Celery

from shared.fundit_common import Settings

settings = Settings(service_name="notification-celery", service_port=8510)
celery_app = Celery(
    "fundit_notifications",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
)


@celery_app.task(name="fundit.email.send")
def send_email_task(recipient: str, subject: str, body: str) -> dict[str, str]:
    return {
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "status": "queued",
    }
