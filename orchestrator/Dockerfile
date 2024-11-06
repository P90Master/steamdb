FROM python:3.9

COPY ./orchestrator /orchestrator

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

ENTRYPOINT python -m orchestrator.main
