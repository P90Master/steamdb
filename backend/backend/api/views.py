from mongoengine import DoesNotExist
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from api.serializers import GameSerializer, GameUpdateSerializer, GamePackageDataSerializer, GamePackageSerializer
from games.documents import Game


class APIViewExtended(APIView):
    @staticmethod
    def _build_response(serializer):
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GamesView(APIViewExtended):
    serializer_class = GameSerializer

    def get(self, request):
        games = Game.objects.all()
        serializer = self.serializer_class(games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data)
        return self._build_response(serializer)


class GameDetailView(APIViewExtended):
    serializer_class = GameSerializer
    serializer_update_class = GameUpdateSerializer

    def get(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(game)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            # TODO: info log message
            return Response(request_serializer.validated_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
