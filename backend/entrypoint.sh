#!/bin/bash

# TODO: production-ready configuration & get params from .env
# TODO: MOVE uvicorn to main.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-config log_conf.yaml \
  --timeout-keep-alive 30 --workers 1 --limit-concurrency 10
