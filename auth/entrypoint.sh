#!/bin/bash

alembic upgrade head

celery -A auth.celery.beat_app beat --loglevel=error &
celery -A auth.celery.worker_app worker --loglevel=error &
uvicorn auth.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8001} \
  --log-config log_conf.yaml \
  --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-60} \
  --workers ${WORKERS:-4} \
  --limit-concurrency ${LIMIT_CONCURRENCY:-100} \
  --backlog ${BACKLOG_SIZE:-2048} \
  --proxy-headers \
  --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-'*'}
