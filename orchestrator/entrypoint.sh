#!/bin/bash

alembic -c orchestrator/db/alembic.ini upgrade head

python -m orchestrator.messenger &
celery -A orchestrator.celery.beat_app beat --loglevel=error &
celery -A orchestrator.celery.worker_app worker --loglevel=error
