
from django.urls import path
from . import views
app_name = "analytics"

urlpatterns = [

    path('game/<slug:slug>/', views.game_analytics, name='game_analytics'),
]
