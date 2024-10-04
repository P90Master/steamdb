from datetime import datetime

from mongoengine import Document, EmbeddedDocument, fields
from django.conf import settings

from .connections import connection


class PriceStory(EmbeddedDocument):
    timestamp = fields.DateTimeField(required=True, default=datetime.now)
    price = fields.DecimalField(required=True, precision=2)
    discount = fields.IntField(required=True, max_value=100, min_value=0)


class GamePrice(EmbeddedDocument):
    # country_code = fields.StringField(required=True, max_length=3)
    currency = fields.StringField(required=True, max_length=3)
    price_story = fields.EmbeddedDocumentListField(PriceStory)


class Game(Document):
    id = fields.IntField(primary_key=True)
    name = fields.StringField(required=True)
    prices = fields.DictField()

    meta = {"db_alias": settings.MONGO_ALIAS, "collection": "games"}
