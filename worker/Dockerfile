FROM python:3.9

# TODO: special user for worker

# TODO: apt update
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

COPY ./worker /worker

# TODO: entrypoint.sh
ENTRYPOINT celery --app worker.celery_app worker --loglevel=info & python -m worker.main
