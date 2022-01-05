from django.urls import re_path
from .views import levels


urlpatterns = [
    #url(r'(?P<level>\d+)', levels, name="level"),
    re_path(r'(?P<level>\d+)', levels, name="level"),
]
