FROM python:3.12

WORKDIR /worker
COPY . .

COPY requirements.txt .

# TODO: apt update
RUN apt-get update && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

RUN useradd -m worker
RUN chown -R worker:worker /worker
USER worker

RUN chmod +x entrypoint.sh

ENTRYPOINT ./entrypoint.sh
