from django.conf.urls import url
from .views import project_all, project_add, project_delete, project_view, project_update, project_download, generate_pdf


urlpatterns = [
    url(r'manage/', project_all, name='projectsmanage'),
    url(r'_add/', project_add, name='projectsadd'),
    url(r'_delete/(?P<projectid>\d+)', project_delete, name='projectsdelete'),
    url(r'view/(?P<projectid>\d+)', project_view, name='projectsview'),
    url(r'_update/',  project_update, name='projectsupdate'),
    url(r'_download/(?P<projectid>\d+)', project_download, name='projectsdownload'),
    url(r'^generatepdf/(?P<projectid>\S+)$', generate_pdf, name="generate_pdf")
]
