from mongoengine import DoesNotExist
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response

from api.serializers import GameSerializer, GameUpdateSerializer, GamePackageSerializer
from games.documents import Game


class GamesView(APIView):
    serializer_class = GameSerializer

    def get(self, request):
        games = Game.objects.all()
        serializer = self.serializer_class(games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GameDetailView(APIView):
    serializer_class = GameSerializer
    serializer_update_class = GameUpdateSerializer

    # TODO PoC
    @staticmethod
    def _get_game(self, id):
        try:
            game = Game.objects.get(id=id)
        except DoesNotExist:
            # raise 404
            pass

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
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GamesPackageView(APIView):
    serializer_class = GamePackageSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            try:
                game = Game.objects.get(id=serializer.validated_data['id'])
                serializer = self.serializer_class(data=serializer.validated_data, instance=game)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.validated_data, status=status.HTTP_200_OK)

            except DoesNotExist:
                serializer.save()
                return Response(serializer.validated_data, status=status.HTTP_200_OK)

            except ValidationError:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
