from django.conf.urls import url
from .views import projects_all, projects_add


urlpatterns = [
    url(r'view/', projects_all, name='projectsall'),
    url(r'add/', projects_add, name='projectsadd')
]
