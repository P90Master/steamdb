FROM python:3.12

WORKDIR /auth
COPY . .

COPY requirements.txt .

RUN apt-get update && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

RUN mkdir -p /auth/static/admin
RUN cp -r /usr/local/lib/python3.12/site-packages/starlette_admin/statics/* /auth/static/admin

RUN useradd -m auth
RUN chown -R auth:auth /auth
USER auth

RUN chmod +x entrypoint.sh

ENTRYPOINT ./entrypoint.sh
