from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path('announce/<slug:slug>/', views.post_announcement, name='post_announcement'),
    path('developer/<str:username>/announce/', views.post_developer_announcement, name='post_developer_announcement'),
]