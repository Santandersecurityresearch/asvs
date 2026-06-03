import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from user_agents import parse

from projects.models import ProjectMember, ProjectRequirement, Projects
from projects.storage import create_project_template, load_project_template


class ProjectAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='alice', password='password12345')
        self.viewer = User.objects.create_user(username='bob', password='password12345')
        self.partial_match = User.objects.create_user(username='bo', password='password12345')
        self.admin = User.objects.create_user(username='adminuser', password='password12345', is_superuser=True)
        self.project = Projects.objects.create(
            project_name='Payments',
            project_owner='alice',
            project_description='Payment app',
            project_level=2,
            project_allowed_viewers='alice,bob',
        )

    def test_viewer_matching_is_exact(self):
        self.assertTrue(self.project.can_view(self.owner))
        self.assertTrue(self.project.can_view(self.viewer))
        self.assertFalse(self.project.can_view(self.partial_match))
        self.assertTrue(self.project.can_manage(self.owner))
        self.assertFalse(self.project.can_manage(self.viewer))
        self.assertTrue(self.project.can_manage(self.admin))

    def test_project_member_editor_can_manage(self):
        ProjectMember.objects.create(project=self.project, username='bob', role=ProjectMember.ROLE_EDITOR)

        self.assertTrue(self.project.can_view(self.viewer))
        self.assertTrue(self.project.can_manage(self.viewer))

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_unauthorized_user_cannot_delete_project_by_id(self):
        user_agent = 'Mozilla/5.0 ASVS-Test'
        device_name = str(parse(user_agent))
        self.viewer.is_two_factor_enabled = True
        self.viewer.save()
        self.viewer.totpdevice_set.create(name=device_name, confirmed=True)
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse('projectsdelete', kwargs={'projectid': self.project.id}),
            HTTP_USER_AGENT=user_agent,
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Projects.objects.filter(id=self.project.id).exists())


class ProjectStorageTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='alice', password='password12345')
        self.project = Projects.objects.create(
            project_name='API',
            project_owner='alice',
            project_description='API app',
            project_level=1,
            project_allowed_viewers='alice',
        )
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def test_project_template_initializes_requirement_state(self):
        requirements = [{
            'req_id': 'V1.1.1',
            'req_description': 'Verify something.',
            'chapter_id': 'V1',
            'chapter_name': 'Architecture',
            'section_id': 'V1.1',
            'section_name': 'Architecture',
            'level1': '✓',
        }]

        with self.settings(BASE_DIR=self.tmpdir.name):
            create_project_template(self.project, requirements)
            data = load_project_template(self.project)

        self.assertEqual(data['project_allowed_viewers'], 'alice')
        self.assertEqual(data['requirements'][0]['enabled'], 0)
        self.assertEqual(data['requirements'][0]['disabled'], 0)
        self.assertEqual(data['requirements'][0]['note'], '')
        self.assertTrue(ProjectRequirement.objects.filter(project=self.project, req_id='V1.1.1').exists())


class ProjectWorkspaceViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='alice', password='password12345')
        self.project = Projects.objects.create(
            project_name='API',
            project_owner='alice',
            project_description='API app',
            project_level=1,
            project_allowed_viewers='alice',
        )
        self.requirement = ProjectRequirement.objects.create(
            project=self.project,
            req_id='V1.1.1',
            req_description='Verify something.',
            chapter_id='V1',
            chapter_name='Architecture',
            section_id='V1.1',
            section_name='Architecture',
        )
        self.user_agent = 'Mozilla/5.0 ASVS-Test'
        self.owner.is_two_factor_enabled = True
        self.owner.save()
        self.owner.totpdevice_set.create(name=str(parse(self.user_agent)), confirmed=True)
        self.client.force_login(self.owner)

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_requirement_autosave_updates_status_and_note(self):
        response = self.client.post(
            reverse('project_requirement_update', kwargs={'projectid': self.project.id, 'req_id': self.requirement.req_id}),
            {'status': ProjectRequirement.STATUS_COMPLETE, 'note': 'Evidence reviewed.'},
            HTTP_USER_AGENT=self.user_agent,
        )

        self.assertEqual(response.status_code, 200)
        self.requirement.refresh_from_db()
        self.assertEqual(self.requirement.status, ProjectRequirement.STATUS_COMPLETE)
        self.assertEqual(self.requirement.note, 'Evidence reviewed.')
        self.assertEqual(response.json()['metrics']['complete'], 1)

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_csv_export_contains_requirements(self):
        response = self.client.get(
            reverse('projectsdownloadcsv', kwargs={'projectid': self.project.id}),
            HTTP_USER_AGENT=self.user_agent,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('V1.1.1', response.content.decode())
