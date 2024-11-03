from datetime import datetime

from mongoengine import DoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.utils.serializer_helpers import ReturnDict

from games.documents import Game, GamePrice, PriceStoryPoint


### For manual use

class PriceStoryPointSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(default=datetime.now)
    discount = serializers.IntegerField(min_value=0, max_value=100, default=0)
    price = serializers.DecimalField(required=True, min_value=0.0, decimal_places=2, max_digits=10)

    def create(self, validated_data):
        validated_data['price'] = float(validated_data['price'])
        return PriceStoryPoint(**validated_data)

    def update(self, instance, validated_data):
        instance.timestamp = validated_data.get('timestamp', instance.timestamp)
        instance.price = float(validated_data.get('price', instance.price))
        instance.discount = validated_data.get('discount', instance.discount)
        return instance


class GamePriceSerializer(serializers.Serializer):
    is_available = serializers.BooleanField(default=True)
    currency = serializers.CharField(required=False, max_length=3)
    price_story = PriceStoryPointSerializer(required=False, many=True)

    def create(self, validated_data):
        return GamePrice(**validated_data)


class GameSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)
    prices = serializers.DictField()

    def create(self, validated_data):
        game_data = {
            "id": validated_data.get('id'),
            "name": validated_data.get('name'),
        }
        game_prices = {}
        for country_code, price_collection in validated_data.get('prices').items():
            game_prices_collection = GamePriceSerializer(data=price_collection)
            game_prices_collection.is_valid(raise_exception=True)
            game_prices[country_code] = game_prices_collection.data

        game_data['prices'] = game_prices
        return Game.objects.create(**game_data)

    def validate_id(self, value):
        try:
            if Game.objects.get(id=value):
                raise ValidationError(f"Game with id '{value}' already exists.")
        except DoesNotExist:
            return value


class GameUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    prices = GamePriceSerializer(many=True, required=False)

    def update(self, instance, validated_data):
        # FIXME actualize
        instance.name = validated_data.get('name', instance.name)

        if new_prices := validated_data.get('prices'):
            current_prices = instance.prices

            for country_code, price_collection in new_prices.items():

                # if country already existed
                if current_country_prices := current_prices.get(country_code):
                    if new_currency := price_collection.get('currency'):
                        current_country_prices.currency = new_currency

                    current_country_prices.price_story.extend(price_collection.get('price_story'))
                    current_country_prices.price_story.sort(key=lambda price_story: price_story.get('timestamp'))
                else:
                    new_price_story = price_collection.get('price_story').sort(
                        key=lambda price_story: price_story.get('timestamp')
                    )
                    new_price_collection = GamePriceSerializer(
                        data={
                            "currency": validated_data.get('currency'),
                            "price_story": new_price_story
                        }
                    )
                    new_price_collection.is_valid(raise_exception=True)
                    current_prices[country_code] = new_price_collection.data

        instance.save()
        return instance


### For autonomous data-collecting tasks

class GamePackageDataSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=False)
    country_code = serializers.CharField(required=True, max_length=3)
    is_available = serializers.BooleanField(default=True)
    currency = serializers.CharField(required=False, max_length=3)
    discount = serializers.IntegerField(min_value=0, max_value=100, default=0)
    price = serializers.DecimalField(required=False, min_value=0.0, decimal_places=2, max_digits=10)
    timestamp = serializers.DateTimeField(default=datetime.now)

    @staticmethod
    def _build_new_price_collection(validated_data: dict) -> ReturnDict:
        if is_available := validated_data.get('is_available'):
            new_price_story_point = PriceStoryPointSerializer(
                data={
                    "timestamp": validated_data.get('timestamp'),
                    "price": validated_data.get('price'),
                    "discount": validated_data.get('discount')
                }
            )
            new_price_story_point.is_valid(raise_exception=True)
            new_price_collection = GamePriceSerializer(
                data={
                    "is_available": is_available,
                    "currency": validated_data.get('currency'),
                    "price_story": [new_price_story_point.data]
                }
            )
            new_price_collection.is_valid(raise_exception=True)
        else:
            new_price_collection = GamePriceSerializer(
                data={
                    "is_available": is_available
                }
            )
            new_price_collection.is_valid(raise_exception=True)
        return new_price_collection.data

    def create(self, validated_data):
        new_price_collection = self._build_new_price_collection(validated_data)
        return Game.objects.create(
            id=validated_data.get('id'),
            name=validated_data.get('name'),
            prices={
                validated_data.get('country_code'): new_price_collection
            }
        )

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        country_code = validated_data.get('country_code')

        # if price collection for received country already exists
        if country_price_collection := instance.prices.get(country_code):

            # if game is available and package contains actual data
            if validated_data.get('is_available'):

                country_price_collection.currency = validated_data.get(
                    'currency',
                    country_price_collection.get("currency")
                )

                # if price changed
                if float(new_price := validated_data.get('price')) != instance.get_current_price(country_code):
                    new_price_story_point = PriceStoryPointSerializer(
                        data={
                            "timestamp": validated_data.get('timestamp'),
                            "price": new_price,
                            "discount": validated_data.get('discount')
                        }
                    )
                    new_price_story_point.is_valid(raise_exception=True)
                    existed_price_story = country_price_collection.get("price_story")
                    existed_price_story.append(new_price_story_point.data)
                    existed_price_story.sort(key=lambda price_story: price_story.get('timestamp'))

            else:

                # if game was available before
                if country_price_collection.get("is_available"):

                    new_price_story_point = PriceStoryPointSerializer(
                        data={
                            "timestamp": validated_data.get('timestamp'),
                            "price": 0.00,
                            "discount": 0
                        }
                    )
                    country_price_collection.is_available = False
                    existed_price_story = country_price_collection.get("price_story")
                    existed_price_story.append(new_price_story_point.data)
                    existed_price_story.sort(key=lambda price_story: price_story.get('timestamp'))

                else:

                    # game was unavailable before and there is no new data in package => do nothing
                    pass

        else:
            new_price_collection = self._build_new_price_collection(validated_data)
            instance.prices[country_code] = new_price_collection

        instance.save()
        return instance


class GamePackageSerializer(serializers.Serializer):
    is_success = serializers.BooleanField(default=True)
    data = GamePackageDataSerializer(required=True)
