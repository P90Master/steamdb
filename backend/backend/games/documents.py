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


# FIXME: change name to App
class Game(Document):
    # TODO: Indexing by type, is_free, developers, publishers

    id = fields.IntField(primary_key=True)
    name = fields.StringField(required=True)
    # TODO: change to EnumField
    type = fields.StringField(required=False, default='')
    short_description = fields.StringField(required=False, default='')
    is_free = fields.BooleanField(required=False, default=False)
    # TODO: split common model to types (Game, DLC, Trailer, etc) & implements specific fields like:
    # dlc = fields.ListField(fields.LazyReferenceField(DLC, reverse_delete_rule=NULLIFY), required=False)
    developers = fields.ListField(fields.StringField(), required=False)
    publishers = fields.ListField(fields.StringField(), required=False)
    total_recommendations = fields.IntField(required=False, default=0)
    prices = fields.DictField()

    def get_current_price(self, country_code: str) -> Union[float, None]:
        if country_code not in self.prices:
            return None

        if not (price_story := self.prices[country_code].get('price_story')):
            return None

        return float(price_story[0].get('price'))

    meta = {"db_alias": settings.MONGO_ALIAS, "collection": "games"}
