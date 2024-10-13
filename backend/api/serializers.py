from datetime import datetime

from mongoengine import DoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from games.documents import Game, GamePrice, PriceStoryPoint


### For manual use
# TODO actualize

class PriceStoryPointSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(default=datetime.now)
    discount = serializers.IntegerField(min_value=0, max_value=100, default=0)
    price = serializers.DecimalField(required=True, min_value=0, decimal_places=2, max_digits=10)

    def create(self, validated_data):
        validated_data['price'] = float(validated_data['price'])
        return PriceStoryPoint(**validated_data)

    def update(self, instance, validated_data):
        instance.timestamp = validated_data.get('timestamp', instance.timestamp)
        instance.price = float(validated_data.get('price', instance.price))
        instance.discount = validated_data.get('discount', instance.discount)
        return instance


class GamePriceSerializer(serializers.Serializer):
    currency = serializers.CharField(required=True, max_length=3)
    price_story = PriceStoryPointSerializer(required=True, many=True)

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
                    new_price_story = price_collection.get('price_story').sort(key=lambda price_story: price_story.get('timestamp'))
                    new_price_collection = GamePrice(
                        currency=price_collection.get('currency'),
                        price_story=new_price_story
                    )
                    current_prices[country_code] = new_price_collection

        instance.save()
        return instance


### For autonomous data-collecting tasks

class GamePackageSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=False)
    country_code = serializers.CharField(required=True, max_length=3)
    currency = serializers.CharField(required=True, max_length=3)
    discount = serializers.IntegerField(min_value=0, max_value=100, default=0)
    price = serializers.DecimalField(required=True, min_value=0, decimal_places=2, max_digits=10)
    timestamp = serializers.DateTimeField(default=datetime.now)

    def create(self, validated_data):
        # TODO reflections: move logic above to view-level
        # TODO Refactor
        # TODO If price the same - do nothing
        new_price_story_point = PriceStoryPoint(
            timestamp=validated_data.get('timestamp'),
            price=validated_data.get('price'),
            discount=validated_data.get('discount')
        )
        new_price_collection = GamePrice(
            currency=validated_data.get('currency'),
            price_story=[new_price_story_point]
        )
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

        if country_price_collection := instance.prices.get(country_code):
            country_price_collection.currency = validated_data.get('currency')
            new_price_story_point = PriceStoryPoint(
                timestamp=validated_data.get('timestamp'),
                price=validated_data.get('price'),
                discount=validated_data.get('discount')
            )
            country_price_collection.price_story.append(new_price_story_point)
            country_price_collection.price_story.sort(key=lambda price_story: price_story.get('timestamp'))
        else:
            new_price_story_point = PriceStoryPoint(
                timestamp=validated_data.get('timestamp'),
                price=validated_data.get('price'),
                discount=validated_data.get('discount')
            )
            new_price_collection = GamePrice(
                currency=validated_data.get('currency'),
                price_story=[new_price_story_point]
            )
            instance.prices[country_code] = new_price_collection

        instance.save()
        return instance
