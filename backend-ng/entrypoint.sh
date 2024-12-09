#!/bin/bash

# TODO: production-ready configuration & get params from .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  --timeout-keep-alive 30 --workers 1 --limit-concurrency 10 --limit-max-requests 100
