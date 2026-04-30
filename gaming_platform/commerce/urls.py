
from django.urls import path
from . import views
app_name = "commerce"

urlpatterns = [

    path("commerce/", views.commerce_view, name="commerce_view"),
    path('add/<int:game_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view , name='cart_view'),
    path('increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

]
