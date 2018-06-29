# Basic setup for allowing users to sign up using a username and a password

from django.conf.urls import url
from .views import signup

urlpatterns = [
    url(r'^signup/$', signup, name='signup'),
]
