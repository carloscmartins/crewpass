from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from events.models import Event
from organizations.access import get_membership, require_manager

from .forms import (
    CompanyForm,
    EventAssignmentForm,
    EventAssignmentShiftForm,
    ShiftForm,
    StaffMemberForm,
    StaffRoleFormSet,
    TeamCategoryForm,
)
from .models import (
    Company,
    EventAssignment,
    EventAssignmentShift,
    Shift,
    StaffMember,
    StaffRole,
    TeamCategory,
)


def _common_context(membership):
    return {
        'organization': membership.organization,
        'membership': membership,
        'can_manage': membership.role in ('ADMIN', 'SUPERVISOR'),
    }


def _save_form(
    request,
    membership,
    form_class,
    instance,
    *,
    title,
    description,
    cancel_url,
    success_url,
    initial=None,
    dependent_role_field=False,
    extra_context=None,
):
    form = form_class(
        request.POST if request.method == 'POST' else None,
        instance=instance,
        organization=membership.organization,
        initial=initial,
    )
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.organization = membership.organization
        record.save()
        messages.success(request, 'Cadastro salvo com sucesso.')
        return redirect(success_url)

    return render(
        request,
        'crud/form.html',
        {
            **_common_context(membership),
            'form': form,
            'page_title': title,
            'page_description': description,
            'cancel_url': cancel_url,
            'dependent_role_field': dependent_role_field,
            **(extra_context or {}),
        },
    )


@login_required
def company_list(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    companies = Company.objects.filter(organization=membership.organization)
    query = request.GET.get('q', '').strip()
    active = request.GET.get('active', '')
    if query:
        companies = companies.filter(
            Q(legal_name__icontains=query)
            | Q(trade_name__icontains=query)
            | Q(contact_name__icontains=query)
        )
    if active in ('1', '0'):
        companies = companies.filter(is_active=(active == '1'))
    rows = [
        {
            'name': company.trade_name or company.legal_name,
            'subtitle': company.legal_name if company.trade_name else company.contact_name,
            'status': 'Ativa' if company.is_active else 'Inativa',
            'active': company.is_active,
            'edit_url': reverse('staff:company_edit', args=[org_slug, company.pk]),
        }
        for company in companies
    ]
    return _directory_response(
        request,
        membership,
        'Empresas',
        'Empresas prestadoras de serviços da organização.',
        rows,
        'staff:company_create',
        query,
        active,
    )


@login_required
def company_create(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    return _company_form(request, membership)


@login_required
def company_edit(request, org_slug, pk):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    company = get_object_or_404(Company, organization=membership.organization, pk=pk)
    return _company_form(request, membership, company)


def _company_form(request, membership, instance=None):
    organization = membership.organization
    return _save_form(
        request,
        membership,
        CompanyForm,
        instance,
        title='Editar empresa' if instance else 'Nova empresa',
        description='Cadastre os dados da empresa prestadora de serviços.',
        cancel_url=reverse('staff:company_list', args=[organization.slug]),
        success_url=reverse('staff:company_list', args=[organization.slug]),
    )


@login_required
def staff_list(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    people = StaffMember.objects.filter(organization=membership.organization)
    query = request.GET.get('q', '').strip()
    active = request.GET.get('active', '')
    if query:
        people = people.filter(
            Q(full_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
        )
    if active in ('1', '0'):
        people = people.filter(is_active=(active == '1'))
    rows = [
        {
            'name': person.full_name,
            'subtitle': person.email or person.phone or 'Sem contato informado',
            'status': 'Ativo' if person.is_active else 'Inativo',
            'active': person.is_active,
            'edit_url': reverse('staff:person_edit', args=[org_slug, person.pk]),
        }
        for person in people
    ]
    return _directory_response(
        request,
        membership,
        'Profissionais',
        'Cadastros reutilizáveis da equipe operacional.',
        rows,
        'staff:person_create',
        query,
        active,
    )


@login_required
def staff_create(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    return _person_form(request, membership)


@login_required
def staff_edit(request, org_slug, pk):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    person = get_object_or_404(StaffMember, organization=membership.organization, pk=pk)
    return _person_form(request, membership, person)


def _person_form(request, membership, instance=None):
    organization = membership.organization
    return _save_form(
        request,
        membership,
        StaffMemberForm,
        instance,
        title='Editar profissional' if instance else 'Novo profissional',
        description='Use somente os dados necessários para a operação; o CPF é opcional. Empresa, categoria e função são definidos ao associar este profissional a um evento.',
        cancel_url=reverse('staff:person_list', args=[organization.slug]),
        success_url=reverse('staff:person_list', args=[organization.slug]),
        dependent_role_field=True,
    )


@login_required
def category_list(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    return _catalog_list(
        request,
        membership,
        TeamCategory,
        'Categorias e funções',
        'staff:category_create',
        'staff:category_edit',
    )


@login_required
def category_create(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    return _category_form(request, membership)


@login_required
def category_edit(request, org_slug, pk):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    category = get_object_or_404(TeamCategory, organization=membership.organization, pk=pk)
    return _category_form(request, membership, category)


@login_required
def category_function_manage(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    category_id = request.GET.get('category_id', '')
    if not category_id.isdigit():
        messages.error(request, 'Selecione a categoria para gerenciar as funções.')
        return redirect('staff:category_list', org_slug=org_slug)
    category = get_object_or_404(
        TeamCategory,
        organization=membership.organization,
        pk=category_id,
        is_active=True,
    )
    return redirect('staff:category_edit', org_slug=org_slug, pk=category.pk)


def _category_form(request, membership, instance=None):
    organization = membership.organization
    form = TeamCategoryForm(
        request.POST if request.method == 'POST' else None,
        instance=instance,
        organization=organization,
    )
    role_queryset = (
        StaffRole.objects.filter(organization=organization, team_category=instance)
        if instance
        else StaffRole.objects.none()
    )
    function_formset = StaffRoleFormSet(
        request.POST if request.method == 'POST' else None,
        instance=instance,
        queryset=role_queryset,
        prefix='functions',
        organization=organization,
    )

    if request.method == 'POST':
        form_is_valid = form.is_valid()
        formset_is_valid = function_formset.is_valid()
        if form_is_valid and formset_is_valid:
            selected_unlinked = list(form.cleaned_data.get('unlinked_roles', []))
            unlinked_names = {role.name.casefold() for role in selected_unlinked}
            inline_names = {
                child_form.cleaned_data.get('name', '').strip().casefold()
                for child_form in function_formset.forms
                if child_form.cleaned_data.get('name', '').strip()
            }
            if unlinked_names & inline_names:
                form.add_error(
                    'unlinked_roles',
                    'Uma função selecionada já existe nesta categoria. Revise a lista.',
                )
            else:
                try:
                    with transaction.atomic():
                        category = form.save(commit=False)
                        category.organization = organization
                        category.save()
                        function_formset.instance = category
                        function_formset.save()
                        for role in selected_unlinked:
                            role.team_category = category
                            role.save(update_fields=['team_category', 'updated_at'])
                except IntegrityError:
                    form.add_error(
                        None,
                        'Não foi possível salvar. Verifique se o grupo e as funções não estão duplicados.',
                    )
                else:
                    messages.success(request, 'Categoria e funções salvas com sucesso.')
                    return redirect(
                        'staff:category_edit',
                        org_slug=organization.slug,
                        pk=category.pk,
                    )

    return render(
        request,
        'crud/form.html',
        {
            **_common_context(membership),
            'form': form,
            'function_formset': function_formset,
            'page_title': 'Editar categoria e funções' if instance else 'Nova categoria e funções',
            'page_description': (
                'Cadastre a categoria e suas funções juntas. Cada função pertence a uma categoria; '
                'a mesma descrição pode ser cadastrada em outra categoria.'
            ),
            'cancel_url': reverse('staff:category_list', args=[organization.slug]),
        },
    )


def _catalog_list(request, membership, model, title, create_url_name, edit_url_name):
    items = model.objects.filter(organization=membership.organization)
    if model is TeamCategory:
        items = items.prefetch_related('staff_roles')
    query = request.GET.get('q', '').strip()
    active = request.GET.get('active', '')
    if query:
        items = items.filter(name__icontains=query)
    if active in ('1', '0'):
        items = items.filter(is_active=(active == '1'))
    rows = []
    for item in items:
        subtitle = ''
        if model is TeamCategory:
            function_count = len(item.staff_roles.all())
            subtitle = f'{function_count} função' + ('' if function_count == 1 else 's')
        rows.append({
            'name': item.name,
            'subtitle': subtitle,
            'status': 'Ativa' if item.is_active else 'Inativa',
            'active': item.is_active,
            'edit_url': reverse(edit_url_name, args=[membership.organization.slug, item.pk]),
            'edit_label': 'Editar categoria e funções' if model is TeamCategory else 'Editar',
        })
    return _directory_response(
        request,
        membership,
        title,
        f'{title} reutilizáveis nos eventos da organização.',
        rows,
        create_url_name,
        query,
        active,
        extra_context=(
            {
                'is_category_directory': True,
                'function_parent_categories': TeamCategory.objects.filter(
                    organization=membership.organization,
                    is_active=True,
                ),
                'manage_functions_url': reverse(
                    'staff:category_function_manage',
                    args=[membership.organization.slug],
                ),
            }
            if model is TeamCategory
            else None
        ),
    )


def _catalog_form(request, membership, form_class, instance, singular, list_route, success_route):
    organization = membership.organization
    return _save_form(
        request,
        membership,
        form_class,
        instance,
        title=f'{"Editar" if instance else "Nova"} {singular.lower()}',
        description=f'Cadastre uma {singular.lower()} reutilizável nesta organização.',
        cancel_url=reverse(list_route, args=[organization.slug]),
        success_url=reverse(success_route, args=[organization.slug]),
    )


def _directory_response(
    request,
    membership,
    title,
    description,
    rows,
    create_url_name,
    query='',
    active='',
    extra_context=None,
):
    return render(
        request,
        'crud/directory_list.html',
        {
            **_common_context(membership),
            'page_title': title,
            'page_description': description,
            'rows': rows,
            'create_url': reverse(create_url_name, args=[membership.organization.slug]),
            'query': query,
            'active_filter': active,
            **(extra_context or {}),
        },
    )


@login_required
def assignment_list(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    organization = membership.organization
    assignments = EventAssignment.objects.filter(organization=organization).select_related(
        'event', 'staff_member', 'company'
    ).prefetch_related('scheduled_shifts')
    query = request.GET.get('q', '').strip()
    event_id = request.GET.get('event', '')
    company_id = request.GET.get('company', '')
    category_id = request.GET.get('category', '')
    role_id = request.GET.get('role', '')
    if query:
        assignments = assignments.filter(
            Q(staff_member__full_name__icontains=query) | Q(event__name__icontains=query)
        )
    for field, value, model in (
        ('event_id', event_id, Event),
        ('company_id', company_id, Company),
        ('team_category_id', category_id, TeamCategory),
        ('staff_role_id', role_id, StaffRole),
    ):
        if value.isdigit():
            selected_id = int(value)
            if model.objects.filter(organization=organization, pk=selected_id).exists():
                assignments = assignments.filter(**{field: selected_id})
    return render(
        request,
        'staff/assignment_list.html',
        {
            **_common_context(membership),
            'assignments': assignments,
            'query': query,
            'event_id': event_id,
            'company_id': company_id,
            'category_id': category_id,
            'role_id': role_id,
            'events': Event.objects.filter(organization=organization),
            'companies': Company.objects.filter(organization=organization),
            'categories': TeamCategory.objects.filter(organization=organization),
            'roles': StaffRole.objects.filter(
                organization=organization,
                team_category__isnull=False,
            ).select_related('team_category').order_by('team_category__name', 'name'),
        },
    )


@login_required
def assignment_create(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    initial = {}
    event_id = request.GET.get('event', '')
    if event_id.isdigit() and Event.objects.filter(
        organization=membership.organization,
        pk=event_id,
    ).exclude(status=Event.Status.CANCELLED).exists():
        initial['event'] = event_id
    return _assignment_form(request, membership, None, initial)


@login_required
def assignment_person_create(request, org_slug, event_id):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = get_object_or_404(
        Event.objects.exclude(status=Event.Status.CANCELLED),
        organization=membership.organization,
        pk=event_id,
    )
    person_form = StaffMemberForm(
        request.POST if request.method == 'POST' else None,
        organization=membership.organization,
        prefix='person',
    )
    assignment_form = EventAssignmentForm(
        request.POST if request.method == 'POST' else None,
        organization=membership.organization,
        include_event_staff=False,
        prefix='assignment',
    )
    shift_form = forms.ModelChoiceField(
        queryset=Shift.objects.filter(
            organization=membership.organization,
            is_active=True,
        ).order_by('name'),
        required=False,
        empty_label='Sem turno previsto',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    shift_value = request.POST.get('shift', '') if request.method == 'POST' else ''
    shift_selected = Shift.objects.filter(
        pk=shift_value,
        organization=membership.organization,
        is_active=True,
    ).first() if shift_value.isdigit() else None

    if request.method == 'POST' and person_form.is_valid() and assignment_form.is_valid():
        try:
            with transaction.atomic():
                person = person_form.save(commit=False)
                person.organization = membership.organization
                person.save()
                assignment = assignment_form.save(commit=False)
                assignment.organization = membership.organization
                assignment.event = event
                assignment.staff_member = person
                assignment.company = person.company
                assignment.status = EventAssignment.Status.ACTIVE
                assignment.save()
                if shift_selected:
                    EventAssignmentShift.objects.create(
                        event_assignment=assignment,
                        shift=shift_selected,
                        created_by=request.user,
                    )
        except IntegrityError:
            assignment_form.add_error(
                None,
                'Não foi possível associar o profissional. Confira se ele já participa deste evento.',
            )
        else:
            messages.success(
                request,
                'Profissional cadastrado e associado ao evento.',
            )
            return redirect(
                f"{reverse('staff:assignment_list', args=[membership.organization.slug])}?event={event.pk}"
            )

    return render(
        request,
        'staff/event_staff_registration.html',
        {
            **_common_context(membership),
            'event': event,
            'person_form': person_form,
            'assignment_form': assignment_form,
            'shift_form': shift_form,
            'shifts': Shift.objects.filter(organization=membership.organization, is_active=True).order_by('name'),
            'shift_selected': shift_selected,
            'cancel_url': reverse(
                'events:detail',
                args=[membership.organization.slug, event.pk],
            ),
        },
    )


@login_required
def assignment_edit(request, org_slug, pk):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    assignment = get_object_or_404(
        EventAssignment,
        organization=membership.organization,
        pk=pk,
    )
    return _assignment_form(request, membership, assignment)


@login_required
def assignment_shifts(request, org_slug, assignment_id):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    assignment = get_object_or_404(
        EventAssignment.objects.select_related('event', 'staff_member'),
        organization=membership.organization,
        event__organization=membership.organization,
        pk=assignment_id,
    )
    can_manage_shifts = (
        assignment.status == EventAssignment.Status.ACTIVE
        and assignment.event.status in (Event.Status.PLANNING, Event.Status.ACTIVE)
    )
    form = EventAssignmentShiftForm(
        request.POST if request.method == 'POST' and can_manage_shifts else None,
        event_assignment=assignment,
    )
    if request.method == 'POST' and can_manage_shifts and form.is_valid():
        shift = form.save(commit=False)
        shift.event_assignment = assignment
        shift.created_by = request.user
        try:
            with transaction.atomic():
                shift.save()
        except IntegrityError:
            form.add_error(
                None,
                'Já existe um turno cadastrado para esta participação. Edite o turno existente.',
            )
        else:
            messages.success(request, 'Turno salvo para esta participação.')
            return redirect(
                'staff:assignment_shifts',
                org_slug=org_slug,
                assignment_id=assignment.pk,
            )

    shifts = assignment.scheduled_shifts.all()
    return render(
        request,
        'staff/assignment_shifts.html',
        {
            **_common_context(membership),
            'assignment': assignment,
            'shifts': shifts,
            'form': form,
            'can_manage_shifts': can_manage_shifts,
            'assignment_list_url': (
                f"{reverse('staff:assignment_list', args=[org_slug])}?event={assignment.event_id}"
            ),
        },
    )


@login_required
def assignment_shift_edit(request, org_slug, assignment_id, shift_id):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    assignment = get_object_or_404(
        EventAssignment.objects.select_related('event', 'staff_member'),
        organization=membership.organization,
        event__organization=membership.organization,
        pk=assignment_id,
    )
    shift = get_object_or_404(
        EventAssignmentShift,
        event_assignment=assignment,
        pk=shift_id,
    )
    can_manage_shifts = (
        assignment.status == EventAssignment.Status.ACTIVE
        and assignment.event.status in (Event.Status.PLANNING, Event.Status.ACTIVE)
    )
    form = EventAssignmentShiftForm(
        request.POST if request.method == 'POST' and can_manage_shifts else None,
        instance=shift,
        event_assignment=assignment,
    )
    if request.method == 'POST' and can_manage_shifts and form.is_valid():
        updated_shift = form.save(commit=False)
        updated_shift.updated_by = request.user
        try:
            with transaction.atomic():
                updated_shift.save()
        except IntegrityError:
            form.add_error(
                None,
                'Já existe um turno cadastrado para esta participação. Edite o turno existente.',
            )
        else:
            messages.success(request, 'Turno atualizado para esta participação.')
            return redirect(
                'staff:assignment_shifts',
                org_slug=org_slug,
                assignment_id=assignment.pk,
            )

    shifts = assignment.scheduled_shifts.all()
    return render(
        request,
        'staff/assignment_shifts.html',
        {
            **_common_context(membership),
            'assignment': assignment,
            'shifts': shifts,
            'form': form,
            'editing_shift': shift,
            'can_manage_shifts': can_manage_shifts,
            'assignment_list_url': (
                f"{reverse('staff:assignment_list', args=[org_slug])}?event={assignment.event_id}"
            ),
            'cancel_edit_url': reverse(
                'staff:assignment_shifts',
                args=[org_slug, assignment.pk],
            ),
        },
    )


@login_required
def shift_list(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    organization = membership.organization
    shifts = Shift.objects.filter(organization=organization).order_by('name')
    return render(
        request,
        'staff/shift_list.html',
        {
            **_common_context(membership),
            'shifts': shifts,
        },
    )


@login_required
def shift_create(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    organization = membership.organization
    return _shift_form(request, membership, None, organization)


@login_required
def shift_edit(request, org_slug, pk):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    organization = membership.organization
    shift = get_object_or_404(Shift, organization=organization, pk=pk)
    return _shift_form(request, membership, shift, organization)


def _shift_form(request, membership, instance, organization):
    return _save_form(
        request,
        membership,
        ShiftForm,
        instance,
        title='Editar turno' if instance else 'Novo turno',
        description='Cadastre um turno reutilizável para a organização. Depois, vincule-o a uma participação.',
        cancel_url=reverse('staff:shift_list', args=[organization.slug]),
        success_url=reverse('staff:shift_list', args=[organization.slug]),
    )


def _assignment_form(request, membership, instance, initial=None):
    organization = membership.organization
    event_id = instance.event_id if instance else (initial or {}).get('event')
    if request.method == 'POST' and request.POST.get('event', '').isdigit():
        event_id = request.POST['event']
    success_url = reverse('staff:assignment_list', args=[organization.slug])
    if event_id and str(event_id).isdigit():
        success_url = f'{success_url}?event={event_id}'
    form = EventAssignmentForm(
        request.POST if request.method == 'POST' else None,
        instance=instance,
        organization=membership.organization,
        initial=initial,
    )
    if request.method == 'POST' and form.is_valid():
        assignment = form.save(commit=False)
        assignment.organization = membership.organization
        if instance is None:
            assignment.event = Event.objects.get(pk=form.cleaned_data['event'].pk)
            assignment.staff_member = form.cleaned_data['staff_member']
        if not instance or not instance.pk:
            assignment.status = EventAssignment.Status.ACTIVE
        shift = form.cleaned_data.get('shift')
        try:
            with transaction.atomic():
                assignment.save()
                if shift:
                    EventAssignmentShift.objects.update_or_create(
                        event_assignment=assignment,
                        defaults={
                            'shift': shift,
                            'created_by': request.user,
                        },
                    )
        except IntegrityError:
            form.add_error(None, 'Não foi possível salvar. Verifique os dados.')
        else:
            messages.success(request, 'Participação salva com sucesso.')
            return redirect(success_url)

    return render(
        request,
        'crud/form.html',
        {
            **_common_context(membership),
            'form': form,
            'page_title': 'Editar participação' if instance else 'Associar profissional a evento',
            'page_description': (
                'Empresa, equipe e função são definidas para esta participação. '
                'Selecione um turno cadastrado ou cadastre um novo.'
            ),
            'cancel_url': reverse('staff:assignment_list', args=[organization.slug]),
            'dependent_role_field': True,
            'shift_catalog_url': reverse('staff:shift_list', args=[organization.slug]),
        },
    )
