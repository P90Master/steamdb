#!/bin/bash

alembic -c orchestrator/db/alembic.ini upgrade head

python -m orchestrator.messenger &
celery -A orchestrator.celery.beat_app beat --loglevel=error &
celery -A orchestrator.celery.worker_app worker --loglevel=error &
# TODO production-ready configuration & get params from .env
uvicorn orchestrator.api.main:app --host 0.0.0.0 --port 8000 --log-config api_log_conf.yaml \
  --timeout-keep-alive 30 --workers 1 --limit-concurrency 10 --limit-max-requests 100
