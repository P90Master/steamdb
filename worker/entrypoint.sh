#!/bin/bash

celery --app worker.celery.celery_app worker --loglevel=error &
python -m worker.messenger
