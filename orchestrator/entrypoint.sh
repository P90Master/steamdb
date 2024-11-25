#!/bin/bash

alembic -c orchestrator/db/alembic.ini upgrade head

python -m orchestrator.messenger &
celery -A orchestrator.celery.beat_app beat --loglevel=error &
celery -A orchestrator.celery.worker_app worker --loglevel=error &
# TODO production-ready configuration & get from .env
uvicorn orchestrator.api.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info --timeout-keep-alive 30 --limit-concurrency 10 --limit-max-requests 100
