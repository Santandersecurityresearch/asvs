from django.contrib import admin

from .models import AuditEvent, ProjectMember, ProjectRequirement, Projects, RequirementComment, RequirementEvidence


@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    list_display = ("id", "project_name", "project_owner", "project_level", "project_created")
    search_fields = ("project_name", "project_owner", "project_description")


@admin.register(ProjectRequirement)
class ProjectRequirementAdmin(admin.ModelAdmin):
    list_display = ("project", "req_id", "chapter_name", "status", "updated_at")
    list_filter = ("status", "chapter_name", "project")
    search_fields = ("req_id", "req_description", "note")


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ("project", "username", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("username", "project__project_name")


@admin.register(RequirementEvidence)
class RequirementEvidenceAdmin(admin.ModelAdmin):
    list_display = ("requirement", "title", "created_by", "created_at")
    search_fields = ("title", "notes", "created_by")


@admin.register(RequirementComment)
class RequirementCommentAdmin(admin.ModelAdmin):
    list_display = ("requirement", "created_by", "created_at")
    search_fields = ("body", "created_by")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("project", "requirement", "actor", "action", "created_at")
    list_filter = ("action",)
    search_fields = ("actor", "action", "detail")
