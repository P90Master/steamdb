#!/bin/bash

alembic -c orchestrator/db/alembic.ini upgrade head

python -m orchestrator.messenger &
celery -A orchestrator.celery.beat_app beat --loglevel=error &
celery -A orchestrator.celery.worker_app worker --loglevel=error &
uvicorn orchestrator.api.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8888} \
  --log-config api_log_conf.yaml \
  --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-60} \
  --workers ${WORKERS:-4} \
  --limit-concurrency ${LIMIT_CONCURRENCY:-4096} \
  --backlog ${BACKLOG_SIZE:-2048} \
  --proxy-headers \
  --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-'*'}
