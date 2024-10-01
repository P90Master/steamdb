from rest_framework import serializers

from games.documents import Game, GamePrice


class GamePriceSerializer(serializers.Serializer):
    country_code = serializers.CharField(required=True, max_length=3)
    currency = serializers.CharField(required=True, max_length=3)
    price = serializers.DecimalField(required=True, min_value=0, decimal_places=2, max_digits=10)

    def create(self, validated_data):
        return GamePrice(**validated_data)


class GameSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    prices = GamePriceSerializer(many=True)

    def create(self, validated_data):
        return Game.objects.create(**validated_data)