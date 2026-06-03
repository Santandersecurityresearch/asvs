from django.urls import re_path
from .views import (
    generate_pdf,
    modify_allowed_users,
    project_add,
    project_all,
    project_delete,
    project_download,
    project_download_csv,
    project_requirement_comment_add,
    project_requirement_evidence_add,
    project_requirement_update,
    project_update,
    project_view,
)


urlpatterns = [
    re_path(r'manage/', project_all, name='projectsmanage'),
    re_path(r'_add/', project_add, name='projectsadd'),
    re_path(r'_delete/(?P<projectid>\d+)', project_delete, name='projectsdelete'),
    re_path(r'view/(?P<projectid>\d+)', project_view, name='projectsview'),
    re_path(r'_update/',  project_update, name='projectsupdate'),
    re_path(r'_download/(?P<projectid>\d+)', project_download, name='projectsdownload'),
    re_path(r'_download_csv/(?P<projectid>\d+)', project_download_csv, name='projectsdownloadcsv'),
    re_path(r'^requirement/(?P<projectid>\d+)/(?P<req_id>[\w.]+)/update$', project_requirement_update, name='project_requirement_update'),
    re_path(r'^requirement/(?P<projectid>\d+)/(?P<req_id>[\w.]+)/evidence$', project_requirement_evidence_add, name='project_requirement_evidence_add'),
    re_path(r'^requirement/(?P<projectid>\d+)/(?P<req_id>[\w.]+)/comment$', project_requirement_comment_add, name='project_requirement_comment_add'),
    re_path(r'^generatepdf/(?P<projectid>\S+)$', generate_pdf, name="generate_pdf"),
    re_path(r'^modifyallowedusers/(?P<projectid>\S+)$', modify_allowed_users, name="modify_allowed_users")
]
