#!/bin/bash

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8000} \
  --log-config log_conf.yaml \
  --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-60} \
  --workers ${WORKERS:-4} \
  --limit-concurrency ${LIMIT_CONCURRENCY:-50} \
  --backlog ${BACKLOG_SIZE:-2048} \
  --proxy-headers \
  --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-'*'}
