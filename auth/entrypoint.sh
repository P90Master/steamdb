#!/bin/bash

alembic upgrade head

celery -A auth.celery.beat_app beat --loglevel=error &
celery -A auth.celery.worker_app worker --loglevel=error &
# TODO: production-ready configuration & get params from .env
uvicorn auth.main:app --host 0.0.0.0 --port 8001 --log-config log_conf.yaml \
  --timeout-keep-alive 30 --workers 1 --limit-concurrency 50 --limit-max-requests 100
