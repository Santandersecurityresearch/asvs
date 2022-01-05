from django.urls import re_path
from .views import project_all, project_add, project_delete, project_view, project_update, project_download, generate_pdf, modify_allowed_users


urlpatterns = [
    re_path(r'manage/', project_all, name='projectsmanage'),
    re_path(r'_add/', project_add, name='projectsadd'),
    re_path(r'_delete/(?P<projectid>\d+)', project_delete, name='projectsdelete'),
    re_path(r'view/(?P<projectid>\d+)', project_view, name='projectsview'),
    re_path(r'_update/',  project_update, name='projectsupdate'),
    re_path(r'_download/(?P<projectid>\d+)', project_download, name='projectsdownload'),
    re_path(r'^generatepdf/(?P<projectid>\S+)$', generate_pdf, name="generate_pdf"),
    re_path(r'^modifyallowedusers/(?P<projectid>\S+)$', modify_allowed_users, name="modify_allowed_users")
]
