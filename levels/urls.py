from django.conf.urls import url
from .views import levels


urlpatterns = [
    url(r'(?P<level>\d+)', levels, name="level"),
]
