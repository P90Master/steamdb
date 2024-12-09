FROM python:3.12

WORKDIR /backend-ng
COPY . .

COPY requirements.txt .

# TODO: apt update
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

RUN chmod +x entrypoint.sh

ENTRYPOINT ./entrypoint.sh
