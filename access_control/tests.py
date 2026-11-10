import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from credentials.models import Credential
from credentials.services import issue_credential, replace_credential
from events.models import Event
from organizations.models import Organization, OrganizationMembership
from staff.forms import EventAssignmentForm
from staff.models import EventAssignment, StaffMember, StaffRole, TeamCategory

from .models import EventOperatorGrant, Movement, MovementCorrection
from .services import (
    grant_event_operator,
    invalidate_latest_movement,
    record_movement,
    revoke_event_operator,
)


class AccessOperationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organização Operação')
        self.admin = User.objects.create_user(
            email='admin-access@example.com',
            password='test-password',
        )
        self.operator = User.objects.create_user(
            email='operator-access@example.com',
            password='test-password',
        )
        self.admin_membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.admin,
            role=OrganizationMembership.Role.ADMIN,
        )
        self.operator_membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.operator,
            role=OrganizationMembership.Role.OPERATOR,
        )
        self.event = Event.objects.create(
            organization=self.organization,
            name='Evento Operacional',
            location='São Paulo',
            starts_at='2027-01-10T18:00:00-03:00',
            ends_at='2027-01-11T02:00:00-03:00',
            status=Event.Status.ACTIVE,
        )
        person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Pessoa Operacional',
            document='123.456.789-01',
        )
        category = TeamCategory.objects.create(
            organization=self.organization,
            name='Produção',
        )
        role = StaffRole.objects.create(
            organization=self.organization,
            team_category=None,
            name='Técnico',
        )
        person.team_category = category
        person.staff_role = role
        person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        self.assignment = EventAssignment.objects.create(
            organization=self.organization,
            event=self.event,
            staff_member=person,
            company=None,
        )
        self.credential = issue_credential(self.assignment, actor=self.admin)

    def grant_operator(self):
        return grant_event_operator(self.event, self.operator_membership, self.admin)[0]

    def operation_url(self):
        return reverse(
            'access_control:operation',
            args=[self.organization.slug, self.event.pk],
        )

    def test_operator_has_no_event_access_until_assigned(self):
        self.client.force_login(self.operator)

        response = self.client.get(
            reverse('access_control:event_list', args=[self.organization.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.event.name)
        self.assertEqual(self.client.get(self.operation_url()).status_code, 403)

    def test_manager_can_grant_event_access_and_operator_can_open_only_that_event(self):
        self.client.force_login(self.admin)
        manage_url = reverse(
            'access_control:operator_management',
            args=[self.organization.slug, self.event.pk],
        )
        response = self.client.post(
            manage_url,
            {
                'intent': 'grant',
                'membership': self.operator_membership.pk,
                'confirm': 'on',
            },
        )

        self.assertRedirects(response, manage_url)
        grant = EventOperatorGrant.objects.get(event=self.event, is_active=True)
        self.assertEqual(grant.membership, self.operator_membership)
        self.assertEqual(grant.granted_by, self.admin)

        self.client.force_login(self.operator)
        response = self.client.get(self.operation_url())
        self.assertContains(response, self.event.name)
        self.assertContains(response, 'access-scanner.js?v=2')

    def test_operator_permission_is_revoked_without_deleting_audit_record(self):
        grant = self.grant_operator()
        revoked = revoke_event_operator(self.event, grant.pk, self.admin)

        self.assertFalse(revoked.is_active)
        self.assertEqual(revoked.revoked_by, self.admin)
        self.assertIsNotNone(revoked.revoked_at)
        self.assertEqual(EventOperatorGrant.objects.count(), 1)

        self.client.force_login(self.operator)
        self.assertEqual(self.client.get(self.operation_url()).status_code, 403)

    def test_regrant_after_revocation_keeps_previous_permission_history(self):
        grant = self.grant_operator()
        revoke_event_operator(self.event, grant.pk, self.admin)

        new_grant, created = grant_event_operator(
            self.event,
            self.operator_membership,
            self.admin,
        )

        self.assertTrue(created)
        self.assertNotEqual(new_grant.pk, grant.pk)
        self.assertEqual(EventOperatorGrant.objects.count(), 2)
        self.assertEqual(EventOperatorGrant.objects.filter(is_active=True).count(), 1)

    def test_manager_can_revoke_operator_access_with_confirmation(self):
        grant = self.grant_operator()
        self.client.force_login(self.admin)
        manage_url = reverse(
            'access_control:operator_management',
            args=[self.organization.slug, self.event.pk],
        )

        response = self.client.post(
            manage_url,
            {'intent': 'revoke', 'grant_id': grant.pk, 'confirm': 'on'},
        )

        self.assertRedirects(response, manage_url)
        grant.refresh_from_db()
        self.assertFalse(grant.is_active)
        self.assertEqual(grant.revoked_by, self.admin)

    def test_operator_cannot_read_cadastros_through_existing_manager_views(self):
        self.grant_operator()
        self.client.force_login(self.operator)

        response = self.client.get(
            reverse('credentials:list', args=[self.organization.slug, self.event.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_manual_search_by_cpf_is_event_scoped_and_does_not_echo_cpf(self):
        self.grant_operator()
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {'intent': 'search', 'query': '123.456.789-01'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pessoa Operacional')
        self.assertNotContains(response, '123.456.789-01')
        self.assertNotIn('123.456.789-01', response.request['PATH_INFO'])
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_manual_search_by_name_shows_only_active_credential_assignments(self):
        self.grant_operator()
        inactive_person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Pessoa sem credencial',
        )
        inactive_person.team_category = self.assignment.staff_member.team_category
        inactive_person.staff_role = self.assignment.staff_member.staff_role
        inactive_person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        inactive_assignment = EventAssignment.objects.create(
            organization=self.organization,
            event=self.event,
            staff_member=inactive_person,
        )
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {'intent': 'search', 'query': 'Pessoa'},
        )

        self.assertContains(response, 'Pessoa Operacional')
        self.assertNotContains(response, 'Pessoa sem credencial')
        self.assertFalse(Credential.objects.filter(event_assignment=inactive_assignment).exists())

    def test_manual_selection_by_name_shows_preview_without_recording_movement(self):
        self.grant_operator()
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {'intent': 'select', 'assignment_id': self.assignment.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credencial identificada')
        self.assertContains(response, self.assignment.staff_member.full_name)
        self.assertContains(response, 'Entrada')
        self.assertFalse(Movement.objects.exists())

    def test_qr_lookup_only_previews_and_never_records_without_confirmation(self):
        self.grant_operator()
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {'intent': 'scan', 'credential_code': self.credential.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pessoa Operacional')
        self.assertContains(response, 'Entrada')
        self.assertNotContains(response, self.credential.code)
        self.assertFalse(Movement.objects.exists())

    def test_suggestion_carries_over_when_active_credential_is_replaced(self):
        record_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            credential_id=self.credential.pk,
            actor=self.admin,
            expected_type=Movement.Type.ENTRY,
            expected_last_movement_id=None,
            request_id=uuid.uuid4(),
        )
        replacement = replace_credential(self.credential, actor=self.admin)
        self.grant_operator()
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {'intent': 'scan', 'credential_code': replacement.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Saída')
        self.assertEqual(Movement.objects.count(), 1)

    def test_scan_rejects_inactive_or_other_event_credentials(self):
        self.grant_operator()
        self.client.force_login(self.operator)
        self.credential.status = Credential.Status.CANCELLED
        self.credential.cancelled_at = self.credential.issued_at
        self.credential.save(update_fields=['status', 'cancelled_at', 'updated_at'])

        response = self.client.post(
            self.operation_url(),
            {'intent': 'scan', 'credential_code': self.credential.code},
        )

        self.assertContains(response, 'Credencial inválida, inativa ou não vinculada a este evento.')
        self.assertNotContains(response, 'Pessoa Operacional')

    def test_only_active_events_allow_operation(self):
        self.event.status = Event.Status.PLANNING
        self.event.save(update_fields=['status', 'updated_at'])
        self.client.force_login(self.admin)

        response = self.client.get(self.operation_url())

        self.assertEqual(response.status_code, 403)

    def test_operator_cannot_select_assignment_outside_authorized_event(self):
        self.grant_operator()
        other_event = Event.objects.create(
            organization=self.organization,
            name='Outro Evento',
            location='Recife',
            starts_at='2027-02-10T18:00:00-03:00',
            ends_at='2027-02-11T02:00:00-03:00',
            status=Event.Status.ACTIVE,
        )
        other_category = TeamCategory.objects.create(
            organization=self.organization,
            name='Equipe Outro',
        )
        other_role = StaffRole.objects.create(
            organization=self.organization,
            team_category=other_category,
            name='Função Outro',
        )
        other_person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Pessoa de Outro Evento',
            team_category=other_category,
            staff_role=other_role,
        )
        other_assignment = EventAssignment.objects.create(
            organization=self.organization,
            event=other_event,
            staff_member=other_person,
        )
        issue_credential(other_assignment, actor=self.admin)
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {'intent': 'select', 'assignment_id': other_assignment.pk},
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'Pessoa de Outro Evento', status_code=404)

    def test_confirmation_records_entry_then_exit_with_actor_and_event(self):
        self.grant_operator()
        self.client.force_login(self.operator)
        first_request = uuid.uuid4()
        response = self.client.post(
            self.operation_url(),
            {
                'intent': 'record',
                'credential_id': self.credential.pk,
                'expected_type': Movement.Type.ENTRY,
                'last_movement_id': '',
                'request_id': first_request,
                'confirm': 'on',
            },
        )

        self.assertRedirects(response, self.operation_url())
        entry = Movement.objects.get()
        self.assertEqual(entry.movement_type, Movement.Type.ENTRY)
        self.assertEqual(entry.recorded_by, self.operator)
        self.assertEqual(entry.event, self.event)

        response = self.client.post(
            self.operation_url(),
            {
                'intent': 'record',
                'credential_id': self.credential.pk,
                'expected_type': Movement.Type.EXIT,
                'last_movement_id': entry.pk,
                'request_id': uuid.uuid4(),
                'confirm': 'on',
            },
        )

        self.assertRedirects(response, self.operation_url())
        self.assertEqual(
            list(Movement.objects.order_by('recorded_at', 'pk').values_list('movement_type', flat=True)),
            [Movement.Type.ENTRY, Movement.Type.EXIT],
        )

    def test_stale_confirmation_is_rejected_and_does_not_duplicate_movement(self):
        self.grant_operator()
        self.client.force_login(self.operator)
        self.client.post(
            self.operation_url(),
            {
                'intent': 'record',
                'credential_id': self.credential.pk,
                'expected_type': Movement.Type.ENTRY,
                'last_movement_id': '',
                'request_id': uuid.uuid4(),
                'confirm': 'on',
            },
        )

        response = self.client.post(
            self.operation_url(),
            {
                'intent': 'record',
                'credential_id': self.credential.pk,
                'expected_type': Movement.Type.ENTRY,
                'last_movement_id': '',
                'request_id': uuid.uuid4(),
                'confirm': 'on',
            },
        )

        self.assertContains(response, 'A situação mudou desde a leitura.')
        self.assertEqual(Movement.objects.count(), 1)

    def test_server_rejects_invalid_override_even_if_client_tampers_with_form(self):
        self.grant_operator()
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {
                'intent': 'record',
                'credential_id': self.credential.pk,
                'expected_type': Movement.Type.EXIT,
                'last_movement_id': '',
                'request_id': uuid.uuid4(),
                'confirm': 'on',
            },
        )

        self.assertContains(response, 'A situação mudou desde a leitura.')
        self.assertFalse(Movement.objects.exists())

    def test_missing_explicit_confirmation_does_not_record_movement(self):
        self.grant_operator()
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {
                'intent': 'record',
                'credential_id': self.credential.pk,
                'expected_type': Movement.Type.ENTRY,
                'last_movement_id': '',
                'request_id': uuid.uuid4(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Movement.objects.exists())

    def test_replayed_confirmation_is_idempotent(self):
        self.grant_operator()
        self.client.force_login(self.operator)
        payload = {
            'intent': 'record',
            'credential_id': self.credential.pk,
            'expected_type': Movement.Type.ENTRY,
            'last_movement_id': '',
            'request_id': uuid.uuid4(),
            'confirm': 'on',
        }
        self.client.post(self.operation_url(), payload)
        response = self.client.post(self.operation_url(), payload)

        self.assertRedirects(response, self.operation_url())
        self.assertEqual(Movement.objects.count(), 1)

    def test_console_does_not_offer_override_for_suggested_movement(self):
        self.grant_operator()
        self.client.force_login(self.operator)

        response = self.client.post(
            self.operation_url(),
            {'intent': 'scan', 'credential_code': self.credential.code},
        )

        self.assertContains(response, 'Entrada')
        self.assertNotContains(response, 'name="movement_type"')

    def test_movement_freezes_assignment_context_fields_in_manager_form(self):
        Movement.objects.create(
            event=self.event,
            event_assignment=self.assignment,
            credential=self.credential,
            movement_type=Movement.Type.ENTRY,
            recorded_by=self.admin,
        )

        form = EventAssignmentForm(
            instance=self.assignment,
            organization=self.organization,
        )

        for field_name in ('event', 'staff_member'):
            self.assertTrue(form.fields[field_name].disabled, field_name)

    def test_correction_preserves_original_and_only_invalidates_latest_valid_movement(self):
        entry, _ = record_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            credential_id=self.credential.pk,
            actor=self.admin,
            expected_type=Movement.Type.ENTRY,
            expected_last_movement_id=None,
            request_id=uuid.uuid4(),
        )
        exit_movement, _ = record_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            credential_id=self.credential.pk,
            actor=self.admin,
            expected_type=Movement.Type.EXIT,
            expected_last_movement_id=entry.pk,
            request_id=uuid.uuid4(),
        )

        with self.assertRaises(ValidationError):
            invalidate_latest_movement(
                event_id=self.event.pk,
                organization_id=self.organization.pk,
                movement_id=entry.pk,
                actor=self.admin,
                reason='Entrada registrada incorretamente.',
            )

        correction = invalidate_latest_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            movement_id=exit_movement.pk,
            actor=self.admin,
            reason='Saída confirmada por engano.',
        )

        self.assertEqual(correction.movement, exit_movement)
        self.assertEqual(correction.corrected_by, self.admin)
        self.assertEqual(Movement.objects.count(), 2)
        self.assertEqual(MovementCorrection.objects.count(), 1)
        latest_valid = Movement.objects.filter(
            event_assignment=self.assignment,
            correction__isnull=True,
        ).latest('recorded_at', 'pk')
        self.assertEqual(latest_valid, entry)

    def test_correction_requires_reason_and_active_manager_membership(self):
        movement, _ = record_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            credential_id=self.credential.pk,
            actor=self.admin,
            expected_type=Movement.Type.ENTRY,
            expected_last_movement_id=None,
            request_id=uuid.uuid4(),
        )
        with self.assertRaises(ValidationError):
            invalidate_latest_movement(
                event_id=self.event.pk,
                organization_id=self.organization.pk,
                movement_id=movement.pk,
                actor=self.admin,
                reason='Erro',
            )

        self.grant_operator()
        with self.assertRaises(PermissionDenied):
            invalidate_latest_movement(
                event_id=self.event.pk,
                organization_id=self.organization.pk,
                movement_id=movement.pk,
                actor=self.operator,
                reason='Correção solicitada por operador.',
            )
