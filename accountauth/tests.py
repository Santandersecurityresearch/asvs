from django.test import TestCase

from accountauth.views import UserCreateForm


class UserCreateFormTests(TestCase):
    def test_signup_form_ignores_client_supplied_privilege_flags(self):
        form = UserCreateForm(data={
            'username': 'mallory',
            'password1': 'Long passphrase 123!',
            'password2': 'Long passphrase 123!',
            'is_superuser': 'on',
            'is_staff': 'on',
            'is_two_factor_enabled': 'on',
        })

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save(commit=False)

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_two_factor_enabled)
