# Basic setup for allowing users to sign up using a username and a password

from django.conf.urls import url
from django.contrib.auth.views import LoginView, LogoutView
from .views import signup, profile

urlpatterns = [
    url(r'^signup/$', signup, name='signup'),
    url(r'login$', LoginView.as_view(
        template_name="auth/login.html"), name="login"),
    url(r'logout$', LogoutView.as_view(), name="logout"),
    url(r'profile', profile, name="profile"),
]
