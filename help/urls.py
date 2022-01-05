from django.urls import re_path
from .views import helping

urlpatterns = [
    #url(r'(?P<category>\d+)', helping, name="help"),
    re_path(r'(?P<category>\d+)', helping, name="help"),
]
