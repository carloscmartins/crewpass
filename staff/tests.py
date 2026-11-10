from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from credentials.services import issue_credential
from events.models import Event
from organizations.models import Organization, OrganizationMembership

from .forms import EventAssignmentForm
from .models import (
    Company,
    EventAssignment,
    EventAssignmentShift,
    Shift,
    StaffMember,
    StaffRole,
    TeamCategory,
)


class StaffManagementTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organização A')
        self.user = User.objects.create_user(email='manager@example.com', password='secret-123')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.ADMIN,
        )
        self.client.force_login(self.user)

    def event(self, organization=None):
        return Event.objects.create(
            organization=organization or self.organization,
            name='Festival',
            location='São Paulo',
            starts_at='2026-12-10T18:00:00-03:00',
            ends_at='2026-12-11T02:00:00-03:00',
        )

    def test_manager_can_create_company_and_search_it(self):
        response = self.client.post(
            reverse('staff:company_create', args=[self.organization.slug]),
            {
                'legal_name': 'Limpeza Exemplo Ltda.',
                'trade_name': 'Limpeza Exemplo',
                'contact_name': 'Ana',
                'phone': '11999990000',
                'email': 'contato@example.com',
                'is_active': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Company.objects.filter(organization=self.organization).exists())

        response = self.client.get(
            reverse('staff:company_list', args=[self.organization.slug]),
            {'q': 'Limpeza Exemplo', 'active': '1'},
        )
        self.assertContains(response, 'Limpeza Exemplo')

    def test_manager_can_create_category_and_function_together_then_assign_professional(self):
        self.client.post(
            reverse('staff:person_create', args=[self.organization.slug]),
            {'full_name': 'Joana Operadora', 'document': '123.456.789-01', 'is_active': 'on'},
        )
        response = self.client.post(
            reverse('staff:category_create', args=[self.organization.slug]),
            {
                'name': 'Segurança',
                'is_active': 'on',
                'functions-TOTAL_FORMS': '1',
                'functions-INITIAL_FORMS': '0',
                'functions-MIN_NUM_FORMS': '0',
                'functions-MAX_NUM_FORMS': '1000',
                'functions-0-name': 'Vigilante',
                'functions-0-is_active': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        event = self.event()
        person = StaffMember.objects.get(organization=self.organization)
        category = TeamCategory.objects.get(organization=self.organization)
        role = StaffRole.objects.get(organization=self.organization, team_category=category)
        person.team_category = category
        person.staff_role = role
        person.save(update_fields=['team_category', 'staff_role', 'updated_at'])

        response = self.client.post(
            reverse('staff:assignment_create', args=[self.organization.slug]),
            {
                'event': event.pk,
                'staff_member': person.pk,
                'company': '',
                'status': EventAssignment.Status.ACTIVE,
                'notes': 'Turno da noite',
            },
        )

        self.assertEqual(response.status_code, 302)
        assignment = EventAssignment.objects.get()
        self.assertEqual(assignment.organization, self.organization)
        self.assertEqual(assignment.notes, 'Turno da noite')
        self.assertEqual(assignment.staff_member.staff_role, role)

    def test_manager_can_register_professional_with_event_category_and_function_in_one_form(self):
        event = self.event()
        category = TeamCategory.objects.create(
            organization=self.organization,
            name='Ambulância',
        )
        role = StaffRole.objects.create(
            organization=self.organization,
            team_category=category,
            name='Enfermeiro',
        )
        registration_url = reverse(
            'staff:assignment_person_create',
            args=[self.organization.slug, event.pk],
        )

        response = self.client.post(
            registration_url,
            {
                'person-full_name': 'Profissional da ambulância',
                'person-document': '',
                'person-phone': '',
                'person-email': '',
                'person-notes': '',
                'person-is_active': 'on',
                'person-team_category': category.pk,
                'person-staff_role': role.pk,
                'assignment-company': '',
                'assignment-notes': '',
            },
        )

        person = StaffMember.objects.get(full_name='Profissional da ambulância')
        assignment = EventAssignment.objects.get(staff_member=person, event=event)
        self.assertRedirects(
            response,
            reverse('staff:assignment_list', args=[self.organization.slug]) + f'?event={event.pk}',
        )
        self.assertEqual(assignment.staff_member.team_category, category)
        self.assertEqual(assignment.staff_member.staff_role, role)
        self.assertEqual(person.event_assignments.count(), 1)

    def test_same_function_name_can_be_registered_under_different_categories(self):
        for category_name in ('Segurança', 'Operação'):
            response = self.client.post(
                reverse('staff:category_create', args=[self.organization.slug]),
                {
                    'name': category_name,
                    'is_active': 'on',
                    'functions-TOTAL_FORMS': '1',
                    'functions-INITIAL_FORMS': '0',
                    'functions-MIN_NUM_FORMS': '0',
                    'functions-MAX_NUM_FORMS': '1000',
                    'functions-0-name': 'Operador',
                    'functions-0-is_active': 'on',
                },
            )
            self.assertEqual(response.status_code, 302)

        functions = StaffRole.objects.filter(
            organization=self.organization,
            name='Operador',
        )
        self.assertEqual(functions.count(), 2)
        self.assertEqual(
            set(functions.values_list('team_category__name', flat=True)),
            {'Segurança', 'Operação'},
        )

    def test_can_add_another_function_to_existing_category_without_recreating_it(self):
        create_response = self.client.post(
            reverse('staff:category_create', args=[self.organization.slug]),
            {
                'name': 'Ambulância',
                'is_active': 'on',
                'functions-TOTAL_FORMS': '1',
                'functions-INITIAL_FORMS': '0',
                'functions-MIN_NUM_FORMS': '0',
                'functions-MAX_NUM_FORMS': '1000',
                'functions-0-name': 'Enfermeiro',
                'functions-0-is_active': 'on',
            },
        )
        category = TeamCategory.objects.get(organization=self.organization, name='Ambulância')
        first_function = StaffRole.objects.get(team_category=category, name='Enfermeiro')
        category_edit_url = reverse(
            'staff:category_edit',
            args=[self.organization.slug, category.pk],
        )
        self.assertRedirects(create_response, category_edit_url)
        category_list_url = reverse('staff:category_list', args=[self.organization.slug])
        category_list = self.client.get(category_list_url)
        self.assertContains(category_list, 'Adicionar função')
        self.assertContains(category_list, 'Ambulância')
        self.assertRedirects(
            self.client.get(
                reverse('staff:category_function_manage', args=[self.organization.slug]),
                {'category_id': category.pk},
            ),
            category_edit_url,
        )

        response = self.client.post(
            category_edit_url,
            {
                'name': 'Ambulância',
                'is_active': 'on',
                'functions-TOTAL_FORMS': '2',
                'functions-INITIAL_FORMS': '1',
                'functions-MIN_NUM_FORMS': '0',
                'functions-MAX_NUM_FORMS': '1000',
                'functions-0-id': first_function.pk,
                'functions-0-name': 'Enfermeiro',
                'functions-0-is_active': 'on',
                'functions-1-name': 'Técnico de enfermagem',
                'functions-1-is_active': 'on',
            },
        )

        self.assertRedirects(response, category_edit_url)
        self.assertEqual(TeamCategory.objects.filter(organization=self.organization).count(), 1)
        self.assertEqual(StaffRole.objects.filter(team_category=category).count(), 2)

    def test_category_form_can_attach_legacy_unlinked_function(self):
        legacy_role = StaffRole.objects.create(
            organization=self.organization,
            name='Função antiga',
        )

        response = self.client.post(
            reverse('staff:category_create', args=[self.organization.slug]),
            {
                'name': 'Produção',
                'is_active': 'on',
                'unlinked_roles': [str(legacy_role.pk)],
                'functions-TOTAL_FORMS': '1',
                'functions-INITIAL_FORMS': '0',
                'functions-MIN_NUM_FORMS': '0',
                'functions-MAX_NUM_FORMS': '1000',
                'functions-0-name': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        legacy_role.refresh_from_db()
        self.assertEqual(legacy_role.team_category.name, 'Produção')

    def test_assignment_form_rejects_references_from_another_organization(self):
        other_organization = Organization.objects.create(name='Organização B')
        event = self.event(other_organization)
        person = StaffMember.objects.create(organization=other_organization, full_name='Pessoa B')
        category = TeamCategory.objects.create(organization=other_organization, name='Equipe B')
        role = StaffRole.objects.create(
            organization=other_organization,
            team_category=None,
            name='Função B',
        )

        form = EventAssignmentForm(
            {
                'event': event.pk,
                'staff_member': person.pk,
                'company': '',
                'status': EventAssignment.Status.ACTIVE,
            },
            organization=self.organization,
        )

        self.assertFalse(form.is_valid())

    def test_issued_credential_locks_event_and_person_on_assignment(self):
        event = self.event()
        other_event = self.event()
        person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Pessoa com credencial',
        )
        other_person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Outra pessoa',
        )
        category = TeamCategory.objects.create(organization=self.organization, name='Equipe')
        role = StaffRole.objects.create(
            organization=self.organization,
            team_category=None,
            name='Função',
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

        form = EventAssignmentForm(
            {
                'event': other_event.pk,
                'staff_member': other_person.pk,
                'company': '',
                'status': EventAssignment.Status.ACTIVE,
                'notes': '',
            },
            instance=assignment,
            organization=self.organization,
        )

        self.assertTrue(form.fields['event'].disabled)
        self.assertTrue(form.fields['staff_member'].disabled)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        assignment.refresh_from_db()
        self.assertEqual(assignment.event, event)
        self.assertEqual(assignment.staff_member, person)

    def test_manager_can_link_overnight_shift_to_assignment(self):
        event = self.event()
        person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Profissional com turno',
        )
        category = TeamCategory.objects.create(organization=self.organization, name='Montagem')
        role = StaffRole.objects.create(
            organization=self.organization,
            team_category=None,
            name='Técnico',
        )
        person.team_category = category
        person.staff_role = role
        person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        assignment = EventAssignment.objects.create(
            organization=self.organization,
            event=event,
            staff_member=person,
        )
        shift_catalog = Shift.objects.create(
            organization=self.organization,
            name='Turno noturno',
            starts_at='20:00',
            ends_at='08:00',
        )
        shifts_url = reverse(
            'staff:assignment_shifts',
            args=[self.organization.slug, assignment.pk],
        )

        response = self.client.post(
            shifts_url,
            {
                'shift': shift_catalog.pk,
            },
        )

        self.assertRedirects(response, shifts_url)
        assignment_shift = EventAssignmentShift.objects.get(event_assignment=assignment)
        self.assertEqual(assignment_shift.created_by, self.user)
        self.assertEqual(assignment_shift.shift, shift_catalog)
        self.assertTrue(assignment_shift.ends_next_day)
        self.assertContains(self.client.get(shifts_url), 'Até o dia seguinte')
        self.assertContains(self.client.get(shifts_url), 'Turno noturno')

        assignment_list_url = reverse('staff:assignment_list', args=[self.organization.slug])
        assignments = self.client.get(assignment_list_url, {'event': event.pk})
        self.assertContains(assignments, 'Gerenciar turno')

    def test_assignment_allows_only_one_shift(self):
        event = self.event()
        person = StaffMember.objects.create(
            organization=self.organization,
            full_name='Profissional com escala',
        )
        category = TeamCategory.objects.create(organization=self.organization, name='Equipe')
        role = StaffRole.objects.create(
            organization=self.organization,
            team_category=None,
            name='Função',
        )
        person.team_category = category
        person.staff_role = role
        person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        assignment = EventAssignment.objects.create(
            organization=self.organization,
            event=event,
            staff_member=person,
        )
        shifts_url = reverse(
            'staff:assignment_shifts',
            args=[self.organization.slug, assignment.pk],
        )
        shift_catalog = Shift.objects.create(
            organization=self.organization,
            name='Turno diurno',
            starts_at='08:00',
            ends_at='20:00',
        )
        response = self.client.post(
            shifts_url,
            {
                'shift': shift_catalog.pk,
            },
        )
        self.assertRedirects(response, shifts_url)
        self.assertEqual(EventAssignmentShift.objects.filter(event_assignment=assignment).count(), 1)

        duplicate_shift = Shift.objects.create(
            organization=self.organization,
            name='Turno noturno',
            starts_at='20:00',
            ends_at='08:00',
        )
        duplicate = self.client.post(
            shifts_url,
            {
                'shift': duplicate_shift.pk,
            },
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertContains(duplicate, 'Turno cadastrado')

    def test_shift_schedule_is_scoped_to_the_assignment_organization(self):
        other_organization = Organization.objects.create(name='Organização B')
        event = self.event(other_organization)
        person = StaffMember.objects.create(
            organization=other_organization,
            full_name='Pessoa B',
        )
        category = TeamCategory.objects.create(organization=other_organization, name='Equipe B')
        role = StaffRole.objects.create(
            organization=other_organization,
            team_category=None,
            name='Função B',
        )
        person.team_category = category
        person.staff_role = role
        person.save(update_fields=['team_category', 'staff_role', 'updated_at'])
        assignment = EventAssignment.objects.create(
            organization=other_organization,
            event=event,
            staff_member=person,
        )

        response = self.client.get(
            reverse(
                'staff:assignment_shifts',
                args=[self.organization.slug, assignment.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_operator_cannot_access_organization_setup_lists_or_create_staff(self):
        operator = User.objects.create_user(email='operator@example.com', password='secret-123')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=operator,
            role=OrganizationMembership.Role.OPERATOR,
        )
        self.client.force_login(operator)

        list_response = self.client.get(
            reverse('staff:person_list', args=[self.organization.slug])
        )
        create_response = self.client.get(
            reverse('staff:person_create', args=[self.organization.slug])
        )

        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(create_response.status_code, 403)

    def test_professional_document_is_unique_inside_organization(self):
        StaffMember.objects.create(
            organization=self.organization,
            full_name='Primeira Pessoa',
            document='12345678901',
        )

        response = self.client.post(
            reverse('staff:person_create', args=[self.organization.slug]),
            {'full_name': 'Pessoa Duplicada', 'document': '123.456.789-01', 'is_active': 'on'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(StaffMember.objects.filter(organization=self.organization).count(), 1)
        self.assertContains(
            response,
            'Já existe um profissional com este CPF nesta organização.',
        )

    def test_assignment_list_ignores_invalid_filter_values(self):
        response = self.client.get(
            reverse('staff:assignment_list', args=[self.organization.slug]),
            {'event': 'not-an-id', 'company': '-1', 'category': '999999'},
        )

        self.assertEqual(response.status_code, 200)
