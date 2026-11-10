import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from access_control.models import Movement, MovementCorrection
from access_control.services import grant_event_operator, invalidate_latest_movement, record_movement
from credentials.services import issue_credential
from events.models import Event
from organizations.models import Organization, OrganizationMembership
from staff.models import Company, EventAssignment, StaffMember, StaffRole, TeamCategory


class EventReportsTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organização Relatórios')
        self.manager = User.objects.create_user(
            email='manager-reports@example.com',
            password='test-password',
            first_name='Supervisora',
            last_name='QA',
        )
        self.operator = User.objects.create_user(
            email='operator-reports@example.com',
            password='test-password',
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.manager,
            role=OrganizationMembership.Role.ADMIN,
        )
        self.operator_membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.operator,
            role=OrganizationMembership.Role.OPERATOR,
        )
        self.event = Event.objects.create(
            organization=self.organization,
            name='Festival de Relatórios',
            location='São Paulo',
            starts_at='2026-11-07T18:00:00-03:00',
            ends_at='2026-11-08T02:00:00-03:00',
            status=Event.Status.ACTIVE,
        )
        self.company = Company.objects.create(
            organization=self.organization,
            legal_name='Produção Segura Ltda.',
            trade_name='Produção Segura',
        )
        self.category = TeamCategory.objects.create(
            organization=self.organization,
            name='Produção',
        )
        self.role = StaffRole.objects.create(
            organization=self.organization,
            team_category=None,
            name='Técnica',
        )

    def create_credentialed_assignment(self, name, document=''):
        person = StaffMember.objects.create(
            organization=self.organization,
            full_name=name,
            document=document,
            phone='11999990000',
            email='private@example.com',
        )
        person.team_category = self.category
        person.staff_role = self.role
        person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        assignment = EventAssignment.objects.create(
            organization=self.organization,
            event=self.event,
            staff_member=person,
            company=self.company,
        )
        credential = issue_credential(assignment, actor=self.manager)
        return assignment, credential

    def record(self, assignment, credential, movement_type, last_movement=None):
        movement, _ = record_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            credential_id=credential.pk,
            actor=self.manager,
            expected_type=movement_type,
            expected_last_movement_id=last_movement.pk if last_movement else None,
            request_id=uuid.uuid4(),
        )
        return movement

    def dashboard_url(self, event=None):
        event = event or self.event
        return reverse('reports:dashboard', args=[self.organization.slug, event.pk])

    def test_dashboard_counts_unique_participations_from_valid_history(self):
        assignment_in = self.create_credentialed_assignment('Ana Presente')
        entry = self.record(*assignment_in, movement_type=Movement.Type.ENTRY)
        self.create_credentialed_assignment('Beto Ainda Não Entrou')
        assignment_out = self.create_credentialed_assignment('Caio Saiu')
        out_entry = self.record(*assignment_out, movement_type=Movement.Type.ENTRY)
        self.record(assignment_out[0], assignment_out[1], Movement.Type.EXIT, out_entry)
        self.client.force_login(self.manager)

        response = self.client.get(self.dashboard_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                key: value
                for key, value in response.context['metrics'].items()
                if key != 'total_presence'
            },
            {
                'credentialed': 3,
                'entered': 2,
                'present': 1,
                'not_entered': 1,
                'exited': 1,
            },
        )
        self.assertRegex(response.context['metrics']['total_presence'], r'^\d+ h \d{2} min$')
        self.assertEqual(response.context['recent_movements'][0].event_assignment, assignment_out[0])
        self.assertEqual(entry.movement_type, Movement.Type.ENTRY)

    def test_dashboard_sums_valid_presence_intervals_and_open_entries(self):
        first_assignment, first_credential = self.create_credentialed_assignment('Ana Presente')
        second_assignment, second_credential = self.create_credentialed_assignment('Beto Saiu')
        invalid_assignment, invalid_credential = self.create_credentialed_assignment('Caio Corrigido')
        as_of = timezone.now()
        base = as_of - timedelta(hours=6)

        first_entry = self.record(first_assignment, first_credential, Movement.Type.ENTRY)
        Movement.objects.filter(pk=first_entry.pk).update(occurred_at=base)
        first_exit = self.record(
            first_assignment,
            first_credential,
            Movement.Type.EXIT,
            first_entry,
        )
        Movement.objects.filter(pk=first_exit.pk).update(
            occurred_at=base + timedelta(hours=2)
        )
        first_reentry = self.record(
            first_assignment,
            first_credential,
            Movement.Type.ENTRY,
            first_exit,
        )
        Movement.objects.filter(pk=first_reentry.pk).update(
            occurred_at=base + timedelta(hours=5)
        )

        second_entry = self.record(second_assignment, second_credential, Movement.Type.ENTRY)
        Movement.objects.filter(pk=second_entry.pk).update(
            occurred_at=base + timedelta(hours=1)
        )
        second_exit = self.record(
            second_assignment,
            second_credential,
            Movement.Type.EXIT,
            second_entry,
        )
        Movement.objects.filter(pk=second_exit.pk).update(
            occurred_at=base + timedelta(hours=2)
        )

        invalid_entry = self.record(
            invalid_assignment,
            invalid_credential,
            Movement.Type.ENTRY,
        )
        Movement.objects.filter(pk=invalid_entry.pk).update(occurred_at=base)
        invalid_exit = self.record(
            invalid_assignment,
            invalid_credential,
            Movement.Type.EXIT,
            invalid_entry,
        )
        Movement.objects.filter(pk=invalid_exit.pk).update(
            occurred_at=base + timedelta(hours=5)
        )
        invalidate_latest_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            movement_id=invalid_exit.pk,
            actor=self.manager,
            reason='Saída registrada incorretamente.',
        )
        invalidate_latest_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            movement_id=invalid_entry.pk,
            actor=self.manager,
            reason='Entrada registrada incorretamente.',
        )
        self.client.force_login(self.manager)

        with patch('reports.services.timezone.now', return_value=as_of):
            response = self.client.get(self.dashboard_url())

        self.assertEqual(response.context['metrics']['total_presence'], '4 h 00 min')
        self.assertContains(response, 'Horas totais de permanência')
        self.assertContains(response, 'não é apuração de jornada')
        periods = response.context['presence_periods']
        self.assertEqual(len(periods), 3)
        self.assertNotIn(invalid_assignment, [period['assignment'] for period in periods])
        open_period = next(period for period in periods if period['exit_at'] is None)
        self.assertEqual(open_period['assignment'], first_assignment)
        self.assertEqual(open_period['entry_at'], base + timedelta(hours=5))
        self.assertContains(response, 'Permanências por profissional')
        self.assertContains(response, 'Em andamento')

    def test_present_list_is_based_on_latest_valid_movement(self):
        self.create_credentialed_assignment('Ana Entrou e Saiu')
        assignment_in = self.create_credentialed_assignment('Beto Presente')
        entry = self.record(*assignment_in, Movement.Type.ENTRY)
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse('reports:present_list', args=[self.organization.slug, self.event.pk])
        )

        self.assertContains(response, 'Beto Presente')
        self.assertNotContains(response, 'Ana Entrou e Saiu')
        self.assertEqual(response.context['page_obj'].object_list[0].latest_movement_id, entry.pk)

    def test_invalidating_latest_movement_recalculates_dashboard_and_presence(self):
        assignment, credential = self.create_credentialed_assignment('Pessoa com correção')
        movement = self.record(assignment, credential, Movement.Type.ENTRY)
        invalidate_latest_movement(
            event_id=self.event.pk,
            organization_id=self.organization.pk,
            movement_id=movement.pk,
            actor=self.manager,
            reason='Entrada registrada por engano.',
        )
        self.client.force_login(self.manager)

        dashboard = self.client.get(self.dashboard_url())
        present = self.client.get(
            reverse('reports:present_list', args=[self.organization.slug, self.event.pk])
        )

        self.assertEqual(dashboard.context['metrics']['entered'], 0)
        self.assertEqual(dashboard.context['metrics']['present'], 0)
        self.assertEqual(dashboard.context['metrics']['not_entered'], 1)
        self.assertNotContains(present, 'Pessoa com correção')

    def test_dashboard_and_history_are_restricted_to_managers(self):
        _, credential = self.create_credentialed_assignment('Pessoa Restrita')
        grant_event_operator(self.event, self.operator_membership, self.manager)
        self.record(
            credential.event_assignment,
            credential,
            Movement.Type.ENTRY,
        )
        self.client.force_login(self.operator)

        dashboard = self.client.get(self.dashboard_url())
        history = self.client.get(
            reverse('reports:history', args=[self.organization.slug, self.event.pk])
        )

        self.assertEqual(dashboard.status_code, 403)
        self.assertEqual(history.status_code, 403)

    def test_reports_list_historical_events_for_managers(self):
        finished = Event.objects.create(
            organization=self.organization,
            name='Evento Encerrado',
            location='Recife',
            starts_at='2026-10-01T18:00:00-03:00',
            ends_at='2026-10-02T02:00:00-03:00',
            status=Event.Status.FINISHED,
        )
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse('reports:event_list', args=[self.organization.slug])
        )

        self.assertContains(response, self.event.name)
        self.assertContains(response, finished.name)

    def test_history_filters_by_person_and_invalidated_status(self):
        assignment, credential = self.create_credentialed_assignment('Pessoa Corrigida')
        movement = self.record(assignment, credential, Movement.Type.ENTRY)
        MovementCorrection.objects.create(
            movement=movement,
            reason='Entrada anotada incorretamente.',
            corrected_by=self.manager,
        )
        self.client.force_login(self.manager)
        history_url = reverse('reports:history', args=[self.organization.slug, self.event.pk])

        response = self.client.get(history_url, {'q': 'Pessoa Corrigida', 'validity': 'corrected'})

        self.assertContains(response, 'Pessoa Corrigida')
        self.assertContains(response, 'Invalidada')
        self.assertContains(response, 'Entrada anotada incorretamente.')
        self.assertEqual(response.context['page_obj'].paginator.count, 1)

    def test_csv_is_filtered_and_excludes_contact_and_document_fields(self):
        assignment, credential = self.create_credentialed_assignment(
            '=Formula Injected Name',
            document='99988877766',
        )
        self.record(assignment, credential, Movement.Type.ENTRY)
        self.client.force_login(self.manager)
        csv_url = reverse('reports:movement_csv', args=[self.organization.slug, self.event.pk])

        response = self.client.get(csv_url, {'q': 'Formula Injected'})

        text = response.content.decode('utf-8-sig')
        self.assertEqual(response.status_code, 200)
        self.assertIn("'=Formula Injected Name", text)
        self.assertIn('Produção Segura', text)
        self.assertNotIn('99988877766', text)
        self.assertNotIn('11999990000', text)
        self.assertNotIn('private@example.com', text)
        self.assertNotIn(credential.code, text)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')

    def test_csv_does_not_export_unfiltered_other_organizations(self):
        other_organization = Organization.objects.create(name='Outra Organização')
        other_event = Event.objects.create(
            organization=other_organization,
            name='Evento Privado',
            location='Curitiba',
            starts_at='2026-11-07T18:00:00-03:00',
            ends_at='2026-11-08T02:00:00-03:00',
        )
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse('reports:movement_csv', args=[self.organization.slug, other_event.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_manager_correction_requires_confirmation_and_preserves_original(self):
        assignment, credential = self.create_credentialed_assignment('Pessoa para corrigir')
        movement = self.record(assignment, credential, Movement.Type.ENTRY)
        correction_url = reverse(
            'access_control:movement_correction',
            args=[self.organization.slug, self.event.pk, movement.pk],
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            correction_url,
            {
                'movement_id': movement.pk,
                'reason': 'Entrada registrada por engano.',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MovementCorrection.objects.filter(movement=movement).exists())

        response = self.client.post(
            correction_url,
            {
                'movement_id': movement.pk,
                'reason': 'Entrada registrada por engano.',
                'confirm': 'on',
            },
        )

        self.assertRedirects(
            response,
            reverse('reports:history', args=[self.organization.slug, self.event.pk]),
        )
        movement.refresh_from_db()
        self.assertTrue(Movement.objects.filter(pk=movement.pk).exists())
        self.assertEqual(movement.correction.corrected_by, self.manager)
        self.assertEqual(movement.correction.reason, 'Entrada registrada por engano.')

    @override_settings(DEBUG=True, ALLOW_NULL_ORIGIN_FOR_LOCAL_DEBUG=True)
    def test_manager_can_correct_from_null_origin_only_with_csrf_token(self):
        assignment, credential = self.create_credentialed_assignment('Pessoa com origem isolada')
        movement = self.record(assignment, credential, Movement.Type.ENTRY)
        correction_url = reverse(
            'access_control:movement_correction',
            args=[self.organization.slug, self.event.pk, movement.pk],
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)

        client.get(correction_url, HTTP_HOST='127.0.0.1:8000')
        csrf_token = client.cookies['csrftoken'].value
        post_data = {
            'movement_id': movement.pk,
            'reason': 'Ajuste em pré-visualização local.',
            'confirm': 'on',
        }
        response = client.post(
            correction_url,
            post_data,
            HTTP_ORIGIN='null',
            HTTP_HOST='127.0.0.1:8000',
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(MovementCorrection.objects.filter(movement=movement).exists())

        post_data['csrfmiddlewaretoken'] = csrf_token
        response = client.post(
            correction_url,
            post_data,
            HTTP_ORIGIN='null',
            HTTP_HOST='127.0.0.1:8000',
        )

        self.assertRedirects(
            response,
            reverse('reports:history', args=[self.organization.slug, self.event.pk]),
        )
        movement.refresh_from_db()
        self.assertEqual(movement.correction.reason, 'Ajuste em pré-visualização local.')

    def test_operator_cannot_open_movement_correction_even_with_event_grant(self):
        assignment, credential = self.create_credentialed_assignment('Pessoa protegida')
        movement = self.record(assignment, credential, Movement.Type.ENTRY)
        grant_event_operator(self.event, self.operator_membership, self.manager)
        self.client.force_login(self.operator)

        response = self.client.get(
            reverse(
                'access_control:movement_correction',
                args=[self.organization.slug, self.event.pk, movement.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_only_latest_valid_history_row_offers_correction(self):
        assignment, credential = self.create_credentialed_assignment('Pessoa com duas ações')
        entry = self.record(assignment, credential, Movement.Type.ENTRY)
        exit_movement = self.record(assignment, credential, Movement.Type.EXIT, entry)
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse('reports:history', args=[self.organization.slug, self.event.pk])
        )

        rows = list(response.context['page_obj'].object_list)
        by_id = {row.pk: row for row in rows}
        self.assertFalse(by_id[entry.pk].can_correct)
        self.assertTrue(by_id[exit_movement.pk].can_correct)
        self.assertContains(response, 'Invalidar se incorreto')
        self.assertContains(response, 'Registros marcados como válidos não precisam de ação.')
        self.assertNotContains(response, 'Corrigir último registro')
