FROM python:3.9

WORKDIR /orchestrator
COPY . .

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

RUN useradd -m orchestrator
RUN chown -R orchestrator:orchestrator /orchestrator
USER orchestrator

RUN chmod +x entrypoint.sh

ENTRYPOINT ./entrypoint.sh
