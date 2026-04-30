
from django.urls import path
from . import views
app_name = "moderation"

urlpatterns = [

    path("moderation/", views.moderation_view, name="moderation_view"),

]
