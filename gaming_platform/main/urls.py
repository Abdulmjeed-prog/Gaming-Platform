from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home_view ,name='home_view'),
    path('upload-test/', views.upload_test_view, name='upload_test'),
]