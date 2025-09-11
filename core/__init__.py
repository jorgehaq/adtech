"""Core package initialization.

Ensure Celery app is loaded when Django starts so that
@shared_task binds to the configured app instead of the
default (which would use the AMQP fallback).
"""

from .celery import app as celery_app  # noqa: F401

__all__ = ("celery_app",)
