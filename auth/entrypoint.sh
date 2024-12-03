#!/bin/bash

# alembic -c auth/db/alembic.ini upgrade head

# TODO production-ready configuration & get params from .env
uvicorn auth.main:app --host 0.0.0.0 --port 8888 \
  --timeout-keep-alive 30 --workers 1 --limit-concurrency 10 --limit-max-requests 100
