from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone


def split_viewers(viewers):
    if not viewers:
        return []
    return [viewer.strip() for viewer in viewers.split(",") if viewer.strip()]


def normalize_viewers(viewers, owner):
    names = split_viewers(viewers)
    if owner and owner not in names:
        names.insert(0, owner)
    return ",".join(dict.fromkeys(names))


class ProjectQuerySet(models.QuerySet):
    def projects_per_user(self, user):
        return self.filter(
            Q(project_owner=user.username)
        )

    def visible_to(self, user):
        if not user.is_authenticated:
            return []
        if user.is_superuser:
            return list(self.all())
        candidates = self.filter(
            Q(project_owner__exact=user.username)
            | Q(project_allowed_viewers__contains=user.username)
        )
        return [project for project in candidates if project.can_view(user)]


class Projects(models.Model):
    project_name = models.CharField(max_length=60)
    project_owner = models.CharField(default=User, max_length=60)
    project_created = models.DateTimeField(auto_now_add=True)
    project_description = models.CharField(max_length=255)
    project_level = models.IntegerField(default=0)
    asvs_version = models.CharField(max_length=20, default="5.0")
    project_allowed_viewers = models.CharField(max_length=6000, blank=True, default="")
    objects = ProjectQuerySet.as_manager()

    def __str__(self):
        return str(self.pk)

    def allowed_viewer_names(self):
        return split_viewers(self.project_allowed_viewers)

    def can_view(self, user):
        if not user.is_authenticated:
            return False
        if user.is_superuser or self.project_owner == user.username:
            return True
        if self.members.filter(username=user.username).exists():
            return True
        return (
            user.username in self.allowed_viewer_names()
        )

    def can_manage(self, user):
        if not user.is_authenticated:
            return False
        if user.is_superuser or self.project_owner == user.username:
            return True
        return self.members.filter(
            username=user.username,
            role__in=[ProjectMember.ROLE_OWNER, ProjectMember.ROLE_EDITOR, ProjectMember.ROLE_REVIEWER],
        ).exists()

    def set_allowed_viewers(self, viewers):
        self.project_allowed_viewers = normalize_viewers(viewers, self.project_owner)


class ProjectMember(models.Model):
    ROLE_OWNER = "owner"
    ROLE_EDITOR = "editor"
    ROLE_REVIEWER = "reviewer"
    ROLE_VIEWER = "viewer"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_EDITOR, "Editor"),
        (ROLE_REVIEWER, "Reviewer"),
        (ROLE_VIEWER, "Viewer"),
    ]

    project = models.ForeignKey(Projects, related_name="members", on_delete=models.CASCADE)
    username = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "username")

    def __str__(self):
        return "{0}:{1}".format(self.project_id, self.username)


class ProjectRequirement(models.Model):
    STATUS_NOT_APPLICABLE = "na"
    STATUS_COMPLETE = "complete"
    STATUS_INCOMPLETE = "incomplete"
    STATUS_NEEDS_REVIEW = "review"
    STATUS_CHOICES = [
        (STATUS_NOT_APPLICABLE, "N/A"),
        (STATUS_COMPLETE, "Complete"),
        (STATUS_INCOMPLETE, "Incomplete"),
        (STATUS_NEEDS_REVIEW, "Needs Review"),
    ]

    project = models.ForeignKey(Projects, related_name="requirements", on_delete=models.CASCADE)
    req_id = models.CharField(max_length=30)
    req_description = models.TextField()
    chapter_id = models.CharField(max_length=20, blank=True, default="")
    chapter_name = models.CharField(max_length=255, blank=True, default="")
    section_id = models.CharField(max_length=30, blank=True, default="")
    section_name = models.CharField(max_length=255, blank=True, default="")
    level1 = models.CharField(max_length=10, blank=True, default="")
    level2 = models.CharField(max_length=10, blank=True, default="")
    level3 = models.CharField(max_length=10, blank=True, default="")
    cwe = models.CharField(max_length=255, blank=True, default="")
    nist = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_APPLICABLE)
    note = models.TextField(blank=True, default="")
    reviewed_by = models.CharField(max_length=150, blank=True, default="")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project", "req_id")
        ordering = ["chapter_id", "section_id", "req_id"]

    def __str__(self):
        return "{0}:{1}".format(self.project_id, self.req_id)

    @property
    def enabled(self):
        return 1 if self.status == self.STATUS_COMPLETE else 0

    @property
    def disabled(self):
        return 1 if self.status == self.STATUS_INCOMPLETE else 0

    def set_status_from_flags(self, enabled=False, disabled=False, needs_review=False):
        if needs_review:
            self.status = self.STATUS_NEEDS_REVIEW
        elif enabled:
            self.status = self.STATUS_COMPLETE
        elif disabled:
            self.status = self.STATUS_INCOMPLETE
        else:
            self.status = self.STATUS_NOT_APPLICABLE

    def mark_reviewed(self, username):
        self.reviewed_by = username
        self.reviewed_at = timezone.now()


class RequirementEvidence(models.Model):
    requirement = models.ForeignKey(ProjectRequirement, related_name="evidence", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class RequirementComment(models.Model):
    requirement = models.ForeignKey(ProjectRequirement, related_name="comments", on_delete=models.CASCADE)
    body = models.TextField()
    created_by = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "{0}:{1}".format(self.requirement_id, self.created_by)


class AuditEvent(models.Model):
    project = models.ForeignKey(Projects, related_name="audit_events", on_delete=models.CASCADE)
    requirement = models.ForeignKey(ProjectRequirement, null=True, blank=True, on_delete=models.SET_NULL)
    actor = models.CharField(max_length=150)
    action = models.CharField(max_length=80)
    detail = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "{0}:{1}".format(self.project_id, self.action)
