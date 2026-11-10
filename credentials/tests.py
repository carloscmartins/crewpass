import base64

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from events.models import Event
from organizations.models import Organization, OrganizationMembership
from staff.models import EventAssignment, StaffMember, StaffRole, TeamCategory

from .models import Credential, CredentialAuditLog
from .qr import qr_svg_data
from .services import cancel_credential, issue_credential, replace_credential


class CredentialManagementTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organização Credencial')
        self.user = User.objects.create_user(email='manager@example.com', password='test-password')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.ADMIN,
        )
        self.event = Event.objects.create(
            organization=self.organization,
            name='Festival Teste',
            location='São Paulo',
            starts_at='2027-01-10T18:00:00-03:00',
            ends_at='2027-01-11T02:00:00-03:00',
        )
        person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Pessoa Confidencial',
            document='12345678901',
        )
        category = TeamCategory.objects.create(
            organization=self.organization,
            name='Equipe de Teste',
        )
        role = StaffRole.objects.create(
            organization=self.organization,
            team_category=None,
            name='Função de Teste',
        )
        person.team_category = category
        person.staff_role = role
        person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        self.assignment = EventAssignment.objects.create(
            organization=self.organization,
            event=self.event,
            staff_member=person,
        )
        self.client.force_login(self.user)

    def test_issued_code_is_unique_unpredictable_and_per_assignment(self):
        credential = issue_credential(self.assignment, actor=self.user)

        self.assertEqual(credential.status, Credential.Status.ACTIVE)
        self.assertEqual(len(credential.code), 43)
        self.assertNotIn(self.assignment.staff_member.full_name, credential.code)
        self.assertNotIn(self.assignment.staff_member.document, credential.code)
        audit = CredentialAuditLog.objects.get(credential=credential)
        self.assertEqual(audit.action, CredentialAuditLog.Action.ISSUED)
        self.assertEqual(audit.actor, self.user)
        with self.assertRaises(ValidationError):
            issue_credential(self.assignment, actor=self.user)

    def test_database_rejects_two_active_credentials_for_one_assignment(self):
        issue_credential(self.assignment, actor=self.user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Credential.objects.create(
                    event_assignment=self.assignment,
                    code='another-random-token',
                    status=Credential.Status.ACTIVE,
                )

        self.assertEqual(
            Credential.objects.filter(
                event_assignment=self.assignment,
                status=Credential.Status.ACTIVE,
            ).count(),
            1,
        )

    def test_cancelled_credential_stays_historical_and_can_be_reissued(self):
        old_credential = issue_credential(self.assignment, actor=self.user)

        cancel_credential(old_credential, actor=self.user)
        replacement = issue_credential(self.assignment, actor=self.user)

        old_credential.refresh_from_db()
        self.assertEqual(old_credential.status, Credential.Status.CANCELLED)
        self.assertIsNotNone(old_credential.cancelled_at)
        self.assertEqual(replacement.status, Credential.Status.ACTIVE)
        self.assertEqual(
            Credential.objects.filter(
                event_assignment=self.assignment,
                status=Credential.Status.ACTIVE,
            ).count(),
            1,
        )
        self.assertEqual(
            list(
                CredentialAuditLog.objects.filter(credential__event_assignment=self.assignment)
                .order_by('action')
                .values_list('action', flat=True)
            ),
            [CredentialAuditLog.Action.CANCELLED, CredentialAuditLog.Action.ISSUED,
             CredentialAuditLog.Action.ISSUED],
        )

    def test_replacement_links_old_and_new_credential(self):
        old_credential = issue_credential(self.assignment, actor=self.user)

        new_credential = replace_credential(old_credential, actor=self.user)

        old_credential.refresh_from_db()
        self.assertEqual(old_credential.status, Credential.Status.REPLACED)
        self.assertEqual(old_credential.replaced_by, new_credential)
        self.assertEqual(new_credential.status, Credential.Status.ACTIVE)
        self.assertNotEqual(old_credential.code, new_credential.code)
        replacement_audit = CredentialAuditLog.objects.get(
            credential=old_credential,
            action=CredentialAuditLog.Action.REPLACED,
        )
        self.assertEqual(replacement_audit.actor, self.user)
        self.assertEqual(replacement_audit.replacement, new_credential)

    def test_qr_svg_contains_only_machine_readable_payload_not_personal_details(self):
        credential = issue_credential(self.assignment, actor=self.user)
        data_uri = qr_svg_data(credential.code)
        svg = base64.b64decode(data_uri.split(',', maxsplit=1)[1]).decode('utf-8')

        self.assertTrue(data_uri.startswith('data:image/svg+xml;base64,'))
        self.assertIn('<svg', svg)
        self.assertNotIn(self.assignment.staff_member.full_name, svg)
        self.assertNotIn(self.assignment.staff_member.document, svg)

    def test_print_view_has_qr_but_does_not_expose_personal_data_or_token(self):
        credential = issue_credential(self.assignment, actor=self.user)
        response = self.client.get(
            reverse(
                'credentials:print',
                args=[self.organization.slug, self.event.pk, credential.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data:image/svg+xml;base64,')
        self.assertNotContains(response, self.assignment.staff_member.full_name)
        self.assertNotContains(response, self.assignment.staff_member.document)
        self.assertNotContains(response, credential.code)

    def test_cancelled_event_cannot_print_an_active_credential(self):
        credential = issue_credential(self.assignment, actor=self.user)
        self.event.status = Event.Status.CANCELLED
        self.event.save(update_fields=['status', 'updated_at'])

        response = self.client.get(
            reverse(
                'credentials:print',
                args=[self.organization.slug, self.event.pk, credential.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse('credentials:list', args=[self.organization.slug, self.event.pk]),
        )

    def test_issue_requires_explicit_confirmation(self):
        issue_url = reverse(
            'credentials:issue',
            args=[self.organization.slug, self.event.pk, self.assignment.pk],
        )

        response = self.client.post(issue_url, {})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Credential.objects.exists())

    def test_issue_confirmation_generates_credential_and_redirects(self):
        issue_url = reverse(
            'credentials:issue',
            args=[self.organization.slug, self.event.pk, self.assignment.pk],
        )

        response = self.client.post(issue_url, {'confirm': 'on'})

        self.assertRedirects(
            response,
            reverse('credentials:list', args=[self.organization.slug, self.event.pk]),
        )
        self.assertEqual(Credential.objects.filter(event_assignment=self.assignment).count(), 1)

    def test_cancel_and_replace_actions_require_explicit_confirmation(self):
        credential = issue_credential(self.assignment, actor=self.user)
        action_url = reverse(
            'credentials:action',
            args=[self.organization.slug, self.event.pk, credential.pk, 'cancel'],
        )

        response = self.client.post(action_url, {})

        self.assertEqual(response.status_code, 200)
        credential.refresh_from_db()
        self.assertEqual(credential.status, Credential.Status.ACTIVE)

    def test_confirmed_cancel_action_updates_status_and_timestamp(self):
        credential = issue_credential(self.assignment, actor=self.user)
        action_url = reverse(
            'credentials:action',
            args=[self.organization.slug, self.event.pk, credential.pk, 'cancel'],
        )

        response = self.client.post(action_url, {'confirm': 'on'})

        self.assertRedirects(
            response,
            reverse('credentials:list', args=[self.organization.slug, self.event.pk]),
        )
        credential.refresh_from_db()
        self.assertEqual(credential.status, Credential.Status.CANCELLED)
        self.assertIsNotNone(credential.cancelled_at)

    def test_confirmed_replace_action_creates_and_links_new_credential(self):
        old_credential = issue_credential(self.assignment, actor=self.user)
        action_url = reverse(
            'credentials:action',
            args=[self.organization.slug, self.event.pk, old_credential.pk, 'replace'],
        )

        response = self.client.post(action_url, {'confirm': 'on'})

        self.assertRedirects(
            response,
            reverse('credentials:list', args=[self.organization.slug, self.event.pk]),
        )
        old_credential.refresh_from_db()
        new_credential = Credential.objects.get(
            event_assignment=self.assignment,
            status=Credential.Status.ACTIVE,
        )
        self.assertEqual(old_credential.status, Credential.Status.REPLACED)
        self.assertEqual(old_credential.replaced_by, new_credential)

    def test_user_cannot_view_credential_from_another_organization(self):
        other_organization = Organization.objects.create(name='Outra organização')
        other_event = Event.objects.create(
            organization=other_organization,
            name='Evento privado',
            location='Recife',
            starts_at='2027-01-10T18:00:00-03:00',
            ends_at='2027-01-11T02:00:00-03:00',
        )
        other_person = StaffMember.objects.create(
            organization=other_organization,
            full_name='Outra Pessoa',
        )
        other_category = TeamCategory.objects.create(
            organization=other_organization,
            name='Outra Equipe',
        )
        other_role = StaffRole.objects.create(
            organization=other_organization,
            team_category=None,
            name='Outra Função',
        )
        other_person.team_category = other_category
        other_person.staff_role = other_role
        other_person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        other_assignment = EventAssignment.objects.create(
            organization=other_organization,
            event=other_event,
            staff_member=other_person,
        )
        credential = issue_credential(other_assignment, actor=self.user)

        response = self.client.get(
            reverse(
                'credentials:print',
                args=[self.organization.slug, other_event.pk, credential.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_cancelled_assignment_or_event_cannot_receive_credential(self):
        self.assignment.status = EventAssignment.Status.CANCELLED
        self.assignment.save(update_fields=['status', 'updated_at'])
        with self.assertRaises(ValidationError):
            issue_credential(self.assignment, actor=self.user)

        self.assignment.status = EventAssignment.Status.ACTIVE
        self.assignment.save(update_fields=['status', 'updated_at'])
        self.event.status = Event.Status.CANCELLED
        self.event.save(update_fields=['status', 'updated_at'])
        with self.assertRaises(ValidationError):
            issue_credential(self.assignment, actor=self.user)
