from django.urls import path, re_path, include

from .views import GamesView, GameDetailView


api_v1_routes = [
    path('games/', GamesView.as_view()),
    re_path(r'games/(?P<game_id>\d+)', GameDetailView.as_view())
]

urlpatterns = [
    path('v1/', include(api_v1_routes)),
]
