from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.urls import reverse


class ProjectQuerySet(models.QuerySet):
    def projects_per_user(self, user):
        return self.filter(
            Q(project_owner=user.username)
        )


class Projects(models.Model):
    project_name = models.CharField(max_length=60)
    project_owner = models.CharField(default=User, max_length=60)
    project_created = models.DateTimeField(auto_now_add=True)
    project_description = models.CharField(max_length=255)
    project_level = models.IntegerField(default=1)

    objects = ProjectQuerySet.as_manager()

    def __str__(self):
        return str(self.pk)
