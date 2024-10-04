from datetime import datetime

from rest_framework import serializers

from games.documents import Game, GamePrice, PriceStory


### For manual use
# TODO actualize

class PriceStorySerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(default=datetime.now)
    discount = serializers.IntegerField(min_value=0, max_value=100, default=0)
    price = serializers.DecimalField(required=True, min_value=0, decimal_places=2, max_digits=10)

    def create(self, validated_data):
        return PriceStory(**validated_data)

    def update(self, instance, validated_data):
        instance.currency = validated_data.get('currency', instance.currency)
        instance.price = validated_data.get('price', instance.price)
        instance.country_code = validated_data.get('country_code', instance.country_code)
        return instance


class GamePriceSerializer(serializers.Serializer):
    country_code = serializers.CharField(required=True, max_length=3)
    currency = serializers.CharField(required=True, max_length=3)
    price_story = PriceStorySerializer(required=True, many=True)


    def create(self, validated_data):
        return GamePrice(**validated_data)

    def update(self, instance, validated_data):
        instance.currency = validated_data.get('currency', instance.currency)
        instance.price = validated_data.get('price', instance.price)
        instance.country_code = validated_data.get('country_code', instance.country_code)
        return instance


class GameSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)
    prices = GamePriceSerializer(many=True)

    def create(self, validated_data):
        return Game.objects.create(**validated_data)


class GameUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    prices = GamePriceSerializer(many=True, required=False)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        if new_prices := validated_data.get('prices'):
            instance.prices = [GamePrice(**price) for price in new_prices]

        instance.save()
        return instance


### For autonomous data-collecting tasks

class GameDataPackageSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=False)
    country_code = serializers.CharField(required=True, max_length=3)
    currency = serializers.CharField(required=True, max_length=3)
    discount = serializers.IntegerField(min_value=0, max_value=100, default=0)
    price = serializers.DecimalField(required=True, min_value=0, decimal_places=2, max_digits=10)
    timestamp = serializers.DateTimeField(default=datetime.now)

    def create(self, validated_data):
        # TODO implement
        # if game not exists => create Game document
        # if game exists, but new country => add GamePrice to "prices" DictField
        # if game exists, country exists and price differs from previous => add PriceStory to "price_story" of GamePrice
        # if game exists, country exists and same price => do nothing
        # TODO reflections: move logic above to view-level
        pass
