from django.urls import include, re_path
from .views import home_page


urlpatterns = [
    #url(r'^$', home_page, name="home"),
re_path(r'^$', home_page, name="home"),
]
