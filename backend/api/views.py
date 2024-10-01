from mongoengine import DoesNotExist
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from api.serializers import GameSerializer
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