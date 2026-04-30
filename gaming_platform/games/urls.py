from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('create_game/', views.create_game, name='create_game'),
    path('all_games/', views.all_games, name='all_games'),
    path('<slug:slug>/', views.game_detail, name='game_detail'),
]