
from django.urls import path
from . import views
app_name = "notifications"

urlpatterns = [

    path("notifications/", views.notifications_view, name="notifications_view"),

]
