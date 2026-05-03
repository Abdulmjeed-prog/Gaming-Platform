from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup_view'),
    path('login/', views.login_view, name="login_view"),
    path('logout/', views.logout_view, name='logout_view'),
    path('developer/', views.developer_dashboard, name='developer_dashboard'),
    path('signup_dev/', views.developer_signup_view, name='developer_signup_view'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/<str:username>/', views.developer_profile_view, name='developer_profile'),
    path('follow/<int:developer_id>/', views.follow_toggle_view, name='follow_toggle'),
    path('my_orders/', views.my_orders_view, name='my_orders_view'),

]