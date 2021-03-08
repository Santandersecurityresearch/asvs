# Basic setup for allowing users to sign up using a username and a password. 

from django.conf.urls import url
from django.contrib.auth.views import LoginView, LogoutView
from .views import signup, TOTPVerifyView, authenticate_2fa, profile, modify_password, custom_logout, modify_username
from django.urls import re_path
from .import views


urlpatterns = [
    re_path(r'^totp/create/$', views.TOTPCreateView.as_view(), name='totp-create'),
    re_path(r'^totp/login/$', views.TOTPVerifyView.as_view() , name='totp-login'),
    url(r'^authenticate_2fa/$',authenticate_2fa, name='authenticate_2fa'),
    url(r'^signup/$', signup, name='signup'),
    url(r'login$', LoginView.as_view(
        template_name="auth/login.html"), name="login"),
    url(r'logout$', custom_logout, name="logout"),
    url(r'profile', profile, name="profile"),
    url(r'modify_password$', modify_password, name="modify_password"),  
    url(r'modify_username$', modify_username, name="modify_username"),
]
