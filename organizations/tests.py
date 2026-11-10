from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Organization, OrganizationMembership


class OrganizationAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='member@example.com', password='pass-1234')
        self.other_user = User.objects.create_user(
            email='outsider@example.com',
            password='pass-1234',
        )
        self.organization = Organization.objects.create(name='Equipe Exemplo')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.ADMIN,
        )

    def test_dashboard_only_lists_active_memberships(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('organizations:dashboard'))

        self.assertContains(response, self.organization.name)

    def test_member_can_open_organization(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('organizations:detail', args=[self.organization.slug])
        )

        self.assertEqual(response.status_code, 200)

    def test_non_member_cannot_open_organization_by_slug(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse('organizations:detail', args=[self.organization.slug])
        )

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse('organizations:dashboard'))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('organizations:dashboard')}",
        )
