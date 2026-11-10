from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from credentials.services import issue_credential
from organizations.models import Organization, OrganizationMembership
from staff.models import EventAssignment, StaffMember, StaffRole, TeamCategory

from .models import Event


class EventManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@example.com', password='secret-123')
        self.organization = Organization.objects.create(name='Organização A')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.ADMIN,
        )
        self.client.force_login(self.user)

    def event_data(self, **overrides):
        return {
            'name': 'Festival Crew',
            'description': 'Evento de teste',
            'location': 'São Paulo',
            'starts_at': '2026-12-10T18:00',
            'ends_at': '2026-12-11T02:00',
            'status': Event.Status.PLANNING,
            **overrides,
        }

    def test_manager_can_create_event(self):
        response = self.client.post(
            reverse('events:create', args=[self.organization.slug]),
            self.event_data(),
        )

        self.assertEqual(response.status_code, 302)
        event = Event.objects.get(name='Festival Crew')
        self.assertEqual(event.organization, self.organization)
        self.assertEqual(event.ends_at.day, 11)

    def test_event_rejects_end_before_start(self):
        response = self.client.post(
            reverse('events:create', args=[self.organization.slug]),
            self.event_data(ends_at='2026-12-10T17:00'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.exists())
        self.assertContains(response, 'O término deve ser posterior ao início.')

    def test_event_list_search_and_status_filter(self):
        Event.objects.create(
            organization=self.organization,
            name='Festival Crew',
            location='São Paulo',
            starts_at='2026-12-10T18:00:00-03:00',
            ends_at='2026-12-11T02:00:00-03:00',
            status=Event.Status.ACTIVE,
        )
        Event.objects.create(
            organization=self.organization,
            name='Feira Técnica',
            location='Campinas',
            starts_at='2026-12-12T18:00:00-03:00',
            ends_at='2026-12-12T23:00:00-03:00',
            status=Event.Status.PLANNING,
        )

        response = self.client.get(
            reverse('events:list', args=[self.organization.slug]),
            {'q': 'Festival', 'status': Event.Status.ACTIVE},
        )

        self.assertContains(response, 'Festival Crew')
        self.assertNotContains(response, 'Feira Técnica')

    def test_other_organization_event_is_not_visible(self):
        other_organization = Organization.objects.create(name='Organização B')
        event = Event.objects.create(
            organization=other_organization,
            name='Evento privado',
            location='Recife',
            starts_at='2026-12-10T18:00:00-03:00',
            ends_at='2026-12-11T02:00:00-03:00',
        )

        response = self.client.get(
            reverse('events:detail', args=[self.organization.slug, event.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_event_detail_links_to_credential_management(self):
        event = Event.objects.create(
            organization=self.organization,
            name='Evento com credenciamento',
            location='Curitiba',
            starts_at='2026-12-10T18:00:00-03:00',
            ends_at='2026-12-11T02:00:00-03:00',
        )

        response = self.client.get(
            reverse('events:detail', args=[self.organization.slug, event.pk])
        )

        self.assertContains(
            response,
            reverse('credentials:list', args=[self.organization.slug, event.pk]),
        )
        self.assertContains(
            response,
            reverse('staff:assignment_create', args=[self.organization.slug]),
        )
        self.assertEqual(response.context['active_assignment_count'], 0)
        self.assertEqual(response.context['active_credential_count'], 0)
        self.assertContains(response, 'Etapa 1 · Equipe')
        self.assertContains(response, 'A operação ficará disponível quando o evento estiver ativo.')

    def test_event_detail_shows_assignment_and_credential_progress(self):
        event = Event.objects.create(
            organization=self.organization,
            name='Evento em operação',
            location='Curitiba',
            starts_at='2026-12-10T18:00:00-03:00',
            ends_at='2026-12-11T02:00:00-03:00',
            status=Event.Status.ACTIVE,
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
        person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Profissional de teste',
        )
        person.team_category = category
        person.staff_role = role
        person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        assignment = EventAssignment.objects.create(
            organization=self.organization,
            event=event,
            staff_member=person,
        )
        issue_credential(assignment, actor=self.user)

        response = self.client.get(
            reverse('events:detail', args=[self.organization.slug, event.pk])
        )

        self.assertEqual(response.context['active_assignment_count'], 1)
        self.assertEqual(response.context['active_credential_count'], 1)
        self.assertContains(response, '1 de 1 participações com credencial ativa.')
        self.assertContains(
            response,
            reverse('access_control:operation', args=[self.organization.slug, event.pk]),
        )
