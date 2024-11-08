from mongoengine import DoesNotExist
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from api.serializers import GameSerializer, GameUpdateSerializer, GamePackageDataSerializer, GamePackageSerializer
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
    def _get_game(id):
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
    package_serializer_class = GamePackageDataSerializer
    request_serializer_class = GamePackageSerializer

    def post(self, request):
        request_serializer = self.request_serializer_class(data=request.data)

        if request_serializer.is_valid():
            package_data = request_serializer.validated_data['data']

            if request_serializer.validated_data['is_success']:
                try:
                    game = Game.objects.get(id=package_data['id'])
                    package_serializer = self.package_serializer_class(data=package_data, instance=game)

                except DoesNotExist:
                    package_serializer = self.package_serializer_class(data=package_data)

                if package_serializer.is_valid():
                    package_serializer.save()
                    return Response(request_serializer.validated_data, status=status.HTTP_200_OK)

                return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            try:
                game = Game.objects.get(id=package_data['id'])
                package_data["is_available"] = False
                package_serializer = self.package_serializer_class(data=package_data, instance=game)
                if package_serializer.is_valid():
                    package_serializer.save()
                    return Response(request_serializer.validated_data, status=status.HTTP_200_OK)

                return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            except DoesNotExist:
                # if task response isn't success and game with given id doesn't exist => may be wrong id - skip
                # TODO Warning log message
                return Response(request_serializer.validated_data, status=status.HTTP_200_OK)

        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
