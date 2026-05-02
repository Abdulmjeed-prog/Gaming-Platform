from django.urls import path, re_path
from . import views

app_name = 'library'

urlpatterns = [
    path('library/', views.library_view, name='library_view'),
    path('play/<slug:slug>/', views.play_game, name='play_game'),
    path('play/<slug:slug>/save/', views.save_progress, name='save_progress'),
    re_path(r'^play-file/(?P<slug>[\w-]+)/(?P<path>.+)$', views.serve_game_file, name='serve_game_file'),
]