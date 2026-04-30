
from django.urls import path
from . import views
app_name = "social"

urlpatterns = [

    path("social/", views.social_view, name="social_view"),

]
