FROM python:3.12

WORKDIR /etl
COPY . .

COPY requirements.txt .

RUN apt-get update && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

RUN chmod +x entrypoint.sh

ENTRYPOINT ./entrypoint.sh
