FROM python:3.12

WORKDIR /backend
COPY . .

RUN apt-get update && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

RUN chmod +x entrypoint.sh

ENTRYPOINT ./entrypoint.sh
