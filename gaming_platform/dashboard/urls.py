from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/games/add/', views.admin_add_key_game_view, name='admin_add_key_game'),
    path('admin-dashboard/games/', views.admin_games_list_view, name='admin_games_list'),
    path('<slug:slug>/add-key/', views.add_game_key_view, name='add_game_key'),
]