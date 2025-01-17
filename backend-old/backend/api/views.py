from mongoengine import DoesNotExist
from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from api.serializers import (
    # Games ######################
    GameSerializer,
    GameActualPriceSerializer,
    GameUpdateSerializer,
    GamePackageDataSerializer,
    GamePackageSerializer,
    # Tasks ######################
    UpdateAppDataTaskSerializer,
    BulkUpdateAppDataTaskSerializer,
)
from api.filters import GameOrderingFilterSet, GameFilterSet
from games.documents import Game
from external_api import OrchestratorAPIClient


class APIViewExtended(APIView):
    @staticmethod
    def _build_response(serializer):
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GamePagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class GamePricesPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class GamesView(APIViewExtended):
    serializer_class = GameSerializer
    serializer_last_price_class = GameActualPriceSerializer
    paginator = GamePagination()
    ordering_filterset = GameOrderingFilterSet()
    filterset = GameFilterSet()

    def _convert_game_price_collection_to_last_price_only(self, game):
        new_price_collection = {}

        for country_code, price_collection in game.prices.items():
            if price_story := price_collection.get("price_story"):
                actual_price = price_story[-1]
                actual_collection = {
                    "is_available": price_collection.get("is_available"),
                    "currency": price_collection.get("currency"),
                    "price": actual_price.get("price"),
                    "discount": actual_price.get("discount"),
                    "last_updated": actual_price.get("timestamp")
                }
            else:
                actual_collection = {
                    "is_available": price_collection.get("is_available"),
                    "currency": price_collection.get("currency"),
                }

            serializer = self.serializer_last_price_class(data=actual_collection)
            serializer.is_valid(raise_exception=True)
            new_price_collection[country_code] = serializer.data

        game.prices = new_price_collection
        return game

    def get(self, request):
        all_games = Game.objects.all()

        filtered_games = self.filterset.filter_queryset(request=request, queryset=all_games, view=self)
        sorted_games = self.ordering_filterset.filter_queryset(request=request, queryset=filtered_games, view=self)
        paginated_games = self.paginator.paginate_queryset(sorted_games, request)
        games_with_actual_price_only = [
            self._convert_game_price_collection_to_last_price_only(game) for game in paginated_games
        ]
        serializer = self.serializer_class(games_with_actual_price_only, many=True)

        return self.paginator.get_paginated_response(serializer.data)

    def post(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data)
        return self._build_response(serializer)


class GameDetailView(APIViewExtended):
    serializer_class = GameSerializer
    serializer_update_class = GameUpdateSerializer
    paginator = GamePricesPagination()

    @staticmethod
    def _cut_prices_by_paginator(game, request, paginator):
        # TODO: Now pagination is common for all countries at once
        for country_code, price_collection in game.prices.items():
            if price_story := price_collection.get('price_story'):
                price_collection['price_story'] = paginator.paginate_queryset(price_story, request)

        return game

    def _get_paginated_game_response(self, game, request):
        paginated_game = self._cut_prices_by_paginator(game, request, self.paginator)
        serializer = self.serializer_class(paginated_game)
        return self.paginator.get_paginated_response(serializer.data)

    def get(self, request, game_id):
        cache_key = f'game_detail_{game_id}'
        cached_game_data = cache.get(cache_key)

        if cached_game_data:
            return self._get_paginated_game_response(cached_game_data, request)

        try:
            game = Game.objects.get(id=game_id)
        except DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        cache.set(cache_key, game, timeout=settings.CACHE_TIMEOUT)
        return self._get_paginated_game_response(game, request)

    def delete(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        game.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_update_class(game, data=request.data)
        return self._build_response(serializer)


class GamesPackageView(APIViewExtended):
    package_serializer_class = GamePackageDataSerializer
    request_serializer_class = GamePackageSerializer

    def _update_or_create_game(self, package_data):
        try:
            game = Game.objects.get(id=package_data['id'])
            return self.package_serializer_class(data=package_data, instance=game)

        except DoesNotExist:
            return self.package_serializer_class(data=package_data)

    def post(self, request):
        request_serializer = self.request_serializer_class(data=request.data)

        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        package_data = request_serializer.validated_data['data']

        if request_serializer.validated_data['is_success']:
            package_serializer = self._update_or_create_game(package_data)
            return self._build_response(package_serializer)

        try:
            game = Game.objects.get(id=package_data['id'])
            package_data["is_available"] = False
            package_serializer = self.package_serializer_class(data=package_data, instance=game)
            return self._build_response(package_serializer)

        except DoesNotExist:
            # if task response isn't success and game with given id doesn't exist => may be wrong id - skip
            return Response(request_serializer.validated_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


### Tasks #############################################################################

orchestrator_client = OrchestratorAPIClient()


def build_task_response(response_collection):
    if status.is_success(response_collection.get('status')):
        return Response(response_collection.get('data', {}), status=status.HTTP_201_CREATED)

    return Response(response_collection.get('data', {}), status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST',])
def update_app_data_task(request):
    serializer = UpdateAppDataTaskSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    response_collection = orchestrator_client.register_update_app_data_task(
        app_id=serializer.validated_data['app_id'],
        country_code=serializer.validated_data['country_code']
    )
    return build_task_response(response_collection)


@api_view(['POST',])
def bulk_update_app_data_task(request):
    serializer = BulkUpdateAppDataTaskSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    response_collection = orchestrator_client.register_bulk_update_app_data_task(
        app_ids=serializer.validated_data['app_ids'],
        country_codes=serializer.validated_data['country_codes']
    )
    return build_task_response(response_collection)


@api_view(['POST',])
def update_app_list_task(request):
    response_collection = orchestrator_client.register_update_app_list_task()
    return build_task_response(response_collection)

@api_view(['GET',])
def get_task_status(request, task_id: str):
    response_collection = orchestrator_client.get_task_status(task_id=task_id)
    return build_task_response(response_collection)
