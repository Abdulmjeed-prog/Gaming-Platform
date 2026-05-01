from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup_view'),
    path('login/', views.login_view, name="login_view"),
    path('logout/', views.logout_view, name='logout_view'),
    path('developer/', views.developer_dashboard, name='developer_dashboard'),
    path('signup_dev/', views.developer_signup_view, name='developer_signup_view'),
]