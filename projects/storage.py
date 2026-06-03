import hashlib
import json
import os

from django.conf import settings

from projects.models import ProjectRequirement


def storage_dir():
    return os.path.join(settings.BASE_DIR, "storage")


def project_hash(project):
    return hashlib.sha3_256(
        "{0}{1}".format(project.project_name, project.id).encode("utf-8")
    ).hexdigest()


def template_path(project):
    return os.path.join(storage_dir(), "{0}.json".format(project_hash(project)))


def prepare_requirement(requirement):
    prepared = requirement.copy()
    prepared.setdefault("enabled", 0)
    prepared.setdefault("disabled", 0)
    prepared.setdefault("note", "")
    prepared.setdefault("status", flags_to_status(prepared.get("enabled"), prepared.get("disabled")))
    return prepared


def flags_to_status(enabled, disabled, needs_review=False):
    if needs_review:
        return ProjectRequirement.STATUS_NEEDS_REVIEW
    if enabled:
        return ProjectRequirement.STATUS_COMPLETE
    if disabled:
        return ProjectRequirement.STATUS_INCOMPLETE
    return ProjectRequirement.STATUS_NOT_APPLICABLE


def requirement_to_dict(requirement):
    return {
        "req_id": requirement.req_id,
        "req_description": requirement.req_description,
        "chapter_id": requirement.chapter_id,
        "chapter_name": requirement.chapter_name,
        "section_id": requirement.section_id,
        "section_name": requirement.section_name,
        "level1": requirement.level1,
        "level2": requirement.level2,
        "level3": requirement.level3,
        "cwe": requirement.cwe,
        "nist": requirement.nist,
        "enabled": requirement.enabled,
        "disabled": requirement.disabled,
        "status": requirement.status,
        "note": requirement.note,
        "reviewed_by": requirement.reviewed_by,
        "reviewed_at": requirement.reviewed_at.isoformat() if requirement.reviewed_at else "",
        "evidence_count": requirement.evidence.count() if requirement.pk else 0,
        "comment_count": requirement.comments.count() if requirement.pk else 0,
    }


def sync_project_requirements(project, requirements):
    existing = {item.req_id: item for item in project.requirements.all()}
    seen = set()
    for raw_requirement in requirements:
        requirement = prepare_requirement(raw_requirement)
        seen.add(requirement["req_id"])
        row = existing.get(requirement["req_id"])
        defaults = {
            "req_description": requirement.get("req_description", ""),
            "chapter_id": requirement.get("chapter_id", ""),
            "chapter_name": requirement.get("chapter_name", ""),
            "section_id": requirement.get("section_id", ""),
            "section_name": requirement.get("section_name", ""),
            "level1": requirement.get("level1", ""),
            "level2": requirement.get("level2", ""),
            "level3": requirement.get("level3", ""),
            "cwe": requirement.get("cwe", ""),
            "nist": requirement.get("nist", ""),
            "status": requirement.get("status", ProjectRequirement.STATUS_NOT_APPLICABLE),
            "note": requirement.get("note", ""),
        }
        if row:
            for key, value in defaults.items():
                setattr(row, key, value)
            row.save()
        else:
            ProjectRequirement.objects.create(project=project, req_id=requirement["req_id"], **defaults)
    project.requirements.exclude(req_id__in=seen).delete()


def create_project_template(project, requirements):
    prepared_requirements = [prepare_requirement(requirement) for requirement in requirements]
    sync_project_requirements(project, prepared_requirements)
    data = {
        "project_owner": project.project_owner,
        "project_name": project.project_name,
        "project_id": project.id,
        "project_description": project.project_description,
        "project_created": project.project_created.isoformat(),
        "project_level": project.project_level,
        "asvs_version": project.asvs_version,
        "requirements": prepared_requirements,
        "project_allowed_viewers": project.project_allowed_viewers,
    }
    save_project_template(project, data)


def load_project_template(project):
    requirements = list(project.requirements.prefetch_related("evidence", "comments"))
    if requirements:
        return {
            "project_owner": project.project_owner,
            "project_name": project.project_name,
            "project_id": project.id,
            "project_description": project.project_description,
            "project_created": project.project_created.isoformat(),
            "project_level": project.project_level,
            "asvs_version": project.asvs_version,
            "requirements": [requirement_to_dict(requirement) for requirement in requirements],
            "project_allowed_viewers": project.project_allowed_viewers,
        }

    with open(template_path(project), "r") as template:
        data = json.load(template)
    sync_project_requirements(project, data.get("requirements", []))
    return load_project_template(project)


def save_project_template(project, data):
    sync_project_requirements(project, data.get("requirements", []))
    data = load_project_template(project)
    os.makedirs(storage_dir(), exist_ok=True)
    with open(template_path(project), "w") as template:
        json.dump(data, template, indent=2)


def delete_project_template(project):
    try:
        os.remove(template_path(project))
    except FileNotFoundError:
        pass
