import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from credentials.models import Credential
from events.models import Event
from organizations.access import MANAGER_ROLES, get_membership, require_manager
from organizations.models import OrganizationMembership
from staff.models import EventAssignment

from .forms import (
    GrantOperatorForm,
    ManualSearchForm,
    MovementCorrectionForm,
    MovementConfirmationForm,
    RevokeOperatorForm,
    ScanLookupForm,
)
from .models import EventOperatorGrant, Movement
from .permissions import get_event_access, require_active_user
from .services import (
    grant_event_operator,
    invalidate_latest_movement,
    next_movement_type,
    record_movement,
    revoke_event_operator,
    search_event_assignments,
)


def _display_name(user):
    return ' '.join(part for part in (user.first_name, user.last_name) if part).strip() or f'Usuário #{user.pk}'


def _render_operation(request, membership, event, **extra_context):
    context = {
        'organization': membership.organization,
        'membership': membership,
        'event': event,
        'search_form': ManualSearchForm(),
        'scan_lookup_form': ScanLookupForm(),
        'result_rows': [],
        'selected_credential': None,
        'last_movement': None,
        'expected_type': None,
        'movement_form': None,
        **extra_context,
    }
    response = render(request, 'access_control/operation.html', context)
    response['Cache-Control'] = 'private, no-store'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response


def _active_credential_for_assignment(event, assignment_id):
    assignments = EventAssignment.objects.select_related(
        'staff_member', 'company'
    ).filter(
        organization_id=event.organization_id,
        event=event,
        status=EventAssignment.Status.ACTIVE,
        staff_member__is_active=True,
        staff_member__organization_id=event.organization_id,
        credentials__status=Credential.Status.ACTIVE,
    ).filter(
        Q(company__isnull=True) | Q(company__organization_id=event.organization_id)
    )
    assignment = get_object_or_404(
        assignments,
        pk=assignment_id,
    )
    credential = get_object_or_404(
        Credential.objects.select_related('event_assignment'),
        event_assignment=assignment,
        status=Credential.Status.ACTIVE,
    )
    return assignment, credential


def _active_credential_by_code(event, organization_id, code):
    return Credential.objects.select_related(
        'event_assignment__staff_member',
        'event_assignment__company',
        'event_assignment__staff_member__team_category',
        'event_assignment__staff_member__staff_role',
    ).filter(
        code=code,
        status=Credential.Status.ACTIVE,
        event_assignment__event=event,
        event_assignment__organization_id=organization_id,
        event_assignment__status=EventAssignment.Status.ACTIVE,
        event_assignment__staff_member__is_active=True,
        event_assignment__staff_member__organization_id=organization_id,
    ).filter(
        Q(event_assignment__company__isnull=True)
        | Q(event_assignment__company__organization_id=organization_id)
    ).first()


def _preview_context(credential):
    last_movement = Movement.objects.filter(
        event_assignment=credential.event_assignment,
        correction__isnull=True,
    ).order_by('-recorded_at', '-pk').first()
    expected_type = next_movement_type(last_movement)
    form = MovementConfirmationForm(
        initial={
            'credential_id': credential.pk,
            'expected_type': expected_type,
            'last_movement_id': last_movement.pk if last_movement else None,
            'request_id': uuid.uuid4(),
        }
    )
    return {
        'selected_credential': credential,
        'last_movement': last_movement,
        'expected_type': expected_type,
        'expected_label': Movement.Type(expected_type).label,
        'movement_form': form,
    }


@login_required
def event_list(request, org_slug):
    require_active_user(request)
    membership = get_membership(request, org_slug)
    events = Event.objects.filter(
        organization=membership.organization,
        status=Event.Status.ACTIVE,
    )
    if membership.role not in MANAGER_ROLES:
        if membership.role != OrganizationMembership.Role.OPERATOR:
            raise PermissionDenied('Seu perfil não tem acesso à operação de eventos.')
        events = events.filter(
            operator_grants__membership=membership,
            operator_grants__is_active=True,
        )
    events = events.distinct().order_by('starts_at', 'name')
    response = render(
        request,
        'access_control/event_list.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'events': events,
        },
    )
    response['Cache-Control'] = 'private, no-store'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response


@login_required
def operation(request, org_slug, event_id):
    membership, event = get_event_access(request, org_slug, event_id)
    if request.method == 'GET':
        return _render_operation(request, membership, event)

    intent = request.POST.get('intent', '')
    if intent == 'search':
        form = ManualSearchForm(request.POST)
        if not form.is_valid():
            return _render_operation(
                request,
                membership,
                event,
                search_error='Informe um nome ou o CPF completo com 11 dígitos.',
            )
        try:
            assignments = search_event_assignments(event, form.cleaned_data['query'])
        except ValidationError as error:
            return _render_operation(
                request,
                membership,
                event,
                search_error=' '.join(error.messages),
            )

        search_limited = len(assignments) > 30
        assignments = assignments[:30]
        active_credentials = Credential.objects.filter(
            status=Credential.Status.ACTIVE,
            event_assignment__in=assignments,
        )
        credentials_by_assignment = {
            credential.event_assignment_id: credential
            for credential in active_credentials
        }
        result_rows = [
            {'assignment': assignment, 'credential': credentials_by_assignment[assignment.pk]}
            for assignment in assignments
            if assignment.pk in credentials_by_assignment
        ]
        return _render_operation(
            request,
            membership,
            event,
            result_rows=result_rows,
            search_limited=search_limited,
            searched=True,
        )

    if intent == 'scan':
        form = ScanLookupForm(request.POST)
        if not form.is_valid():
            return _render_operation(
                request,
                membership,
                event,
                operation_error='Não foi possível ler a credencial. Tente novamente ou pesquise pelo nome/CPF.',
            )
        credential = _active_credential_by_code(
            event,
            membership.organization_id,
            form.cleaned_data['credential_code'].strip(),
        )
        if credential is None:
            return _render_operation(
                request,
                membership,
                event,
                operation_error='Credencial inválida, inativa ou não vinculada a este evento.',
            )
        return _render_operation(request, membership, event, **_preview_context(credential))

    if intent == 'select':
        assignment_id = request.POST.get('assignment_id', '')
        if not assignment_id.isdigit():
            return _render_operation(
                request,
                membership,
                event,
                operation_error='Selecione uma participação válida para este evento.',
            )
        _, credential = _active_credential_for_assignment(event, int(assignment_id))
        return _render_operation(request, membership, event, **_preview_context(credential))

    if intent == 'record':
        form = MovementConfirmationForm(request.POST)
        if not form.is_valid():
            error_message = 'Confirme a movimentação para continuar.'
            credential_id = request.POST.get('credential_id', '')
            credential = None
            if credential_id.isdigit():
                credential = _active_credential_by_id(
                    event,
                    membership.organization_id,
                    int(credential_id),
                )
            preview = _preview_context(credential) if credential else {}
            return _render_operation(
                request,
                membership,
                event,
                operation_error=error_message,
                **preview,
            )

        data = form.cleaned_data
        try:
            movement, created = record_movement(
                event_id=event.pk,
                organization_id=membership.organization_id,
                credential_id=data['credential_id'],
                actor=request.user,
                expected_type=data['expected_type'],
                expected_last_movement_id=data['last_movement_id'],
                request_id=data['request_id'],
            )
        except ValidationError as error:
            credential = _active_credential_by_id(
                event,
                membership.organization_id,
                data['credential_id'],
            )
            preview = _preview_context(credential) if credential else {}
            return _render_operation(
                request,
                membership,
                event,
                operation_error=' '.join(error.messages),
                **preview,
            )

        action = movement.get_movement_type_display().lower()
        messages.success(
            request,
            f'{action.capitalize()} registrada para '
            f'{movement.event_assignment.staff_member.full_name}.'
            if created
            else f'Esta confirmação já havia sido registrada como {action}.',
        )
        return redirect('access_control:operation', org_slug=org_slug, event_id=event.pk)

    return _render_operation(
        request,
        membership,
        event,
        operation_error='Ação não reconhecida. Atualize a tela e tente novamente.',
    )


def _active_credential_by_id(event, organization_id, credential_id):
    return Credential.objects.select_related(
        'event_assignment__staff_member',
        'event_assignment__company',
        'event_assignment__staff_member__team_category',
        'event_assignment__staff_member__staff_role',
    ).filter(
        pk=credential_id,
        status=Credential.Status.ACTIVE,
        event_assignment__event=event,
        event_assignment__organization_id=organization_id,
        event_assignment__status=EventAssignment.Status.ACTIVE,
        event_assignment__staff_member__is_active=True,
        event_assignment__staff_member__organization_id=organization_id,
    ).filter(
        Q(event_assignment__company__isnull=True)
        | Q(event_assignment__company__organization_id=organization_id)
    ).first()


@login_required
def operator_management(request, org_slug, event_id):
    require_active_user(request)
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = get_object_or_404(
        Event,
        organization=membership.organization,
        pk=event_id,
    )
    grant_form = GrantOperatorForm(
        request.POST if request.method == 'POST' and request.POST.get('intent') == 'grant' else None,
        organization=membership.organization,
    )
    revoke_form = RevokeOperatorForm(
        request.POST if request.method == 'POST' and request.POST.get('intent') == 'revoke' else None,
    )

    if request.method == 'POST' and request.POST.get('intent') == 'grant':
        if grant_form.is_valid():
            try:
                _, created = grant_event_operator(
                    event,
                    grant_form.cleaned_data['membership'],
                    request.user,
                )
            except ValidationError as error:
                grant_form.add_error(None, error)
            else:
                messages.success(
                    request,
                    'Acesso operacional concedido.' if created else 'Este operador já tem acesso ao evento.',
                )
                return redirect(
                    'access_control:operator_management',
                    org_slug=org_slug,
                    event_id=event.pk,
                )
    elif request.method == 'POST' and request.POST.get('intent') == 'revoke':
        if revoke_form.is_valid():
            try:
                revoke_event_operator(event, revoke_form.cleaned_data['grant_id'], request.user)
            except ValidationError as error:
                revoke_form.add_error(None, error)
            else:
                messages.success(request, 'Acesso operacional revogado.')
                return redirect(
                    'access_control:operator_management',
                    org_slug=org_slug,
                    event_id=event.pk,
                )

    grants = EventOperatorGrant.objects.filter(
        event=event,
        is_active=True,
        membership__organization=membership.organization,
    ).select_related('membership__user', 'granted_by').order_by('membership__user__email')
    response = render(
        request,
        'access_control/operator_management.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'grants': grants,
            'grant_form': grant_form,
            'revoke_form': revoke_form,
            'cancel_url': reverse('events:detail', args=[org_slug, event.pk]),
        },
    )
    response['Cache-Control'] = 'private, no-store'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response


@login_required
def movement_correction(request, org_slug, event_id, movement_id):
    require_active_user(request)
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = get_object_or_404(
        Event,
        pk=event_id,
        organization=membership.organization,
    )
    movement = get_object_or_404(
        Movement.objects.select_related(
            'event_assignment__staff_member',
            'event_assignment__company',
            'event_assignment__staff_member__team_category',
            'event_assignment__staff_member__staff_role',
            'recorded_by',
            'correction',
        ),
        pk=movement_id,
        event=event,
        event_assignment__organization=membership.organization,
    )
    latest_valid = Movement.objects.filter(
        event_assignment=movement.event_assignment,
        correction__isnull=True,
    ).order_by('-recorded_at', '-pk').first()
    correction = getattr(movement, 'correction', None)
    movement.recorded_by_label = _display_name(movement.recorded_by)
    if correction:
        correction.corrected_by_label = _display_name(correction.corrected_by)
    can_correct = (
        correction is None
        and latest_valid is not None
        and latest_valid.pk == movement.pk
    )
    form = MovementCorrectionForm(
        request.POST if request.method == 'POST' and can_correct else None,
        initial={'movement_id': movement.pk},
    )
    correction_error = ''

    if request.method == 'POST' and can_correct:
        if form.is_valid():
            try:
                invalidate_latest_movement(
                    event_id=event.pk,
                    organization_id=membership.organization_id,
                    movement_id=movement.pk,
                    actor=request.user,
                    reason=form.cleaned_data['reason'],
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                messages.success(request, 'Movimentação invalidada com justificativa e histórico preservado.')
                return redirect(
                    'reports:history',
                    org_slug=org_slug,
                    event_id=event.pk,
                )
        else:
            correction_error = 'Confira a justificativa e confirme explicitamente a invalidação.'

    response = render(
        request,
        'access_control/movement_correction.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'movement': movement,
            'form': form,
            'can_correct': can_correct,
            'correction_error': correction_error,
            'history_url': reverse('reports:history', args=[org_slug, event.pk]),
        },
    )
    response['Cache-Control'] = 'private, no-store'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response
