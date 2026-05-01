from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('library/', views.library_view, name='library_view'),
    path('play/<slug:slug>/', views.play_game, name='play_game'),
    path('play/<slug:slug>/save/', views.save_progress, name='save_progress'),
]