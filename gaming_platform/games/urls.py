from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('create_game/', views.create_game, name='create_game'),
    path('all_games/', views.all_games, name='all_games'),
    path('<slug:slug>/', views.game_detail, name='game_detail'),
    
    path('<slug:slug>/edit/',views.edit_game,name='edit_game'),
    path('<slug:slug>/version/add/',views.add_version,name='add_version'),
    path('<slug:slug>/publish/',views.toggle_publish,name='toggle_publish'),
    path('<slug:slug>/version/<int:version_pk>/activate/',views.set_active_version, name='set_active_version'),
    path('media/<int:pk>/delete/',views.delete_media,name='delete_media'),
    path('<slug:slug>/manage/',  views.game_manage,  name='game_manage'),
    path('<slug:slug>/delete/',  views.delete_game,  name='delete_game'),
    path('<slug:slug>/add-key/', views.add_game_key_view, name='add_game_key'),
]