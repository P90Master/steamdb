FROM python:3.9

COPY ./orchestrator /orchestrator

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

ENTRYPOINT alembic -c /orchestrator/db/alembic.ini upgrade head && \
           python -m orchestrator.messenger & \
           celery -A orchestrator.celery.beat_app beat --loglevel=error & \
           celery -A orchestrator.celery.worker_app worker --loglevel=error
