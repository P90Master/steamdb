FROM python:3.12

WORKDIR /orchestrator
COPY . .

COPY requirements.txt .

# TODO: apt update
RUN apt-get update && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

RUN useradd -m orchestrator
RUN chown -R orchestrator:orchestrator /orchestrator
USER orchestrator

RUN chmod +x entrypoint.sh

ENTRYPOINT ./entrypoint.sh
