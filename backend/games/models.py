from mongoengine import Document, EmbeddedDocument, fields
from django.conf import settings

from .connections import connection


class GamePrice(EmbeddedDocument):
    country_code = fields.StringField(required=True, max_length=3)
    currency = fields.StringField(required=True, max_length=3)
    price = fields.DecimalField(required=True, precision=2)

    meta = {"db_alias": settings.MONGO_ALIAS, "collection": "gameprices"}


class Game(Document):
    game_id = fields.StringField(primary_key=True)
    name = fields.StringField(required=True)
    prices = fields.EmbeddedDocumentListField(GamePrice)

    meta = {"db_alias": settings.MONGO_ALIAS, "collection": "games"}
