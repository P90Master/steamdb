from mongoengine import connect

from django.conf import settings

# FIXME db name const
connection = connect(
    host=settings.MONGO_HOST,
    port=settings.MONGO_PORT,
    db='games',
    username=settings.MONGO_USER,
    password=settings.MONGO_PASSWORD,
    authentication_source='admin',
    alias=settings.MONGO_ALIAS,
)
