
from django.urls import path
from . import views
app_name = "commerce"

urlpatterns = [

    path("commerce/", views.commerce_view, name="commerce_view"),

]
