FROM python:3.12

WORKDIR /auth
COPY . .

COPY requirements.txt .

# TODO: apt update
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

RUN useradd -m auth
RUN chown -R auth:auth /auth
USER auth

RUN chmod +x entrypoint.sh

ENTRYPOINT ./entrypoint.sh
