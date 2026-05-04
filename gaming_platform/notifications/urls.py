from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path('inbox/', views.inbox_view, name='inbox'),
    path('mark-read/<int:pk>/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('announce/<slug:slug>/', views.post_announcement, name='post_announcement'),
    path('developer/<str:username>/announce/', views.post_developer_announcement, name='post_developer_announcement'),
]