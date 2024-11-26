FROM python:3.9

WORKDIR /backend

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

COPY backend/ .

# TODO: entrypoint.sh
# TODO: properly configure gunicorn
ENTRYPOINT python3 manage.py migrate && gunicorn backend.wsgi:application --bind 0:8000
