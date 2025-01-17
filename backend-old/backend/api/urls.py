from django.urls import path, re_path, include
from django.conf import settings

from .views import (
    # Games ######################
    GamesView,
    GameDetailView,
    GamesPackageView,
    # Tasks ######################
    update_app_data_task,
    bulk_update_app_data_task,
    update_app_list_task,
    get_task_status,
)


api_v1_routes = [
    path('games/', GamesView.as_view()),
    re_path(r'games/(?P<game_id>\d+)', GameDetailView.as_view()),
    path('games/package/', GamesPackageView.as_view()),
    path('tasks/update_app_data/', update_app_data_task),
    path('tasks/bulk_update_app_data/', bulk_update_app_data_task),
    path('tasks/update_app_list/', update_app_list_task),
    re_path(
        r'^tasks/(?P<task_id>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/$',
        get_task_status
    ),
]

urlpatterns = [
    path(f'{settings.API_VERSION}/', include(api_v1_routes)),
]
