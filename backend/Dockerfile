FROM python:3.9

WORKDIR /backend

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

COPY backend/ .

CMD ["gunicorn", "backend.wsgi:application", "--bind", "0:8000" ]
