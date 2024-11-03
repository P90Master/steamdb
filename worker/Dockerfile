FROM python:3.9

# TODO: special user for worker

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./worker /worker

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# "ls && celery -A celery_app worker --loglevel=info & python -m main"
ENTRYPOINT celery --app worker.celery_app worker --loglevel=info & python -m worker.main
