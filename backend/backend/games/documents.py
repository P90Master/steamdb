from typing import Union

from mongoengine import Document, EmbeddedDocument, fields
from django.conf import settings
from django.utils import timezone

from .connections import connection


class PriceStoryPoint(EmbeddedDocument):
    timestamp = fields.DateTimeField(required=True, default=timezone.now())
    price = fields.DecimalField(required=True, precision=2)
    discount = fields.IntField(required=True, max_value=100, min_value=0)


class GamePrice(EmbeddedDocument):
    is_available = fields.BooleanField(default=True)
    currency = fields.StringField(required=False, max_length=3)
    price_story = fields.EmbeddedDocumentListField(PriceStoryPoint)


class Game(Document):
    id = fields.IntField(primary_key=True)
    name = fields.StringField(required=True)
    prices = fields.DictField()

    def get_current_price(self, country_code: str) -> Union[float, None]:
        if country_code not in self.prices:
            return None

        if not (price_story := self.prices[country_code].get('price_story')):
            return None

        return float(price_story[-1].get('price'))

    meta = {"db_alias": settings.MONGO_ALIAS, "collection": "games"}
