from django.conf.urls import url
from .views import helping

urlpatterns = [
    url(r'(?P<category>\d+)', helping, name="help"),
]
