import csv
from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from access_control.models import Movement
from events.models import Event
from organizations.access import get_membership, require_manager

from .forms import MovementHistoryFilterForm, PresentFilterForm
from .services import (
    assignments_with_last_valid_movement,
    credentialed_assignments,
    event_movements,
    movement_history_for_event,
    presence_periods_for_event,
)


def _manager_event(request, org_slug, event_id):
    if not request.user.is_active:
        raise PermissionDenied('Sua conta não está ativa.')
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = get_object_or_404(
        Event,
        pk=event_id,
        organization=membership.organization,
    )
    return membership, event


def _private_response(response):
    response['Cache-Control'] = 'private, no-store'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response


def _format_duration_label(duration):
    total_minutes = max(0, int(duration.total_seconds() // 60))
    hours, minutes = divmod(total_minutes, 60)
    return f'{hours} h {minutes:02d} min'


@login_required
def event_list(request, org_slug):
    if not request.user.is_active:
        raise PermissionDenied('Sua conta não está ativa.')
    membership = get_membership(request, org_slug)
    require_manager(membership)
    events = Event.objects.filter(
        organization=membership.organization,
    ).order_by('-starts_at', 'name')
    return _private_response(
        render(
            request,
            'reports/event_list.html',
            {
                'organization': membership.organization,
                'membership': membership,
                'events': events,
            },
        )
    )


@login_required
def dashboard(request, org_slug, event_id):
    membership, event = _manager_event(request, org_slug, event_id)
    assignments = assignments_with_last_valid_movement(event)
    presence_periods, total_presence = presence_periods_for_event(event)
    recent_movements = list(
        event_movements(event).order_by('-recorded_at', '-pk')[:10]
    )
    for movement in recent_movements:
        movement.is_valid = getattr(movement, 'correction', None) is None
        movement.recorded_by_label = _user_label(movement.recorded_by)

    metrics = {
        'credentialed': assignments.count(),
        'entered': event_movements(event)
        .filter(movement_type=Movement.Type.ENTRY, correction__isnull=True)
        .values('event_assignment_id')
        .distinct()
        .count(),
        'present': assignments.filter(latest_movement_type=Movement.Type.ENTRY).count(),
        'not_entered': assignments.filter(latest_movement_id__isnull=True).count(),
        'exited': assignments.filter(latest_movement_type=Movement.Type.EXIT).count(),
        'total_presence': _format_duration_label(total_presence),
    }
    response = render(
        request,
        'reports/dashboard.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'metrics': metrics,
            'presence_periods': presence_periods,
            'recent_movements': recent_movements,
        },
    )
    return _private_response(response)


def _apply_present_filters(assignments, cleaned_data):
    query = cleaned_data.get('q', '').strip()
    if query:
        assignments = assignments.filter(
            staff_member__full_name__icontains=query,
        )
    if cleaned_data.get('company'):
        assignments = assignments.filter(company=cleaned_data['company'])
    if cleaned_data.get('category'):
        assignments = assignments.filter(staff_member__team_category=cleaned_data['category'])
    if cleaned_data.get('role'):
        assignments = assignments.filter(staff_member__staff_role=cleaned_data['role'])
    return assignments


@login_required
def present_list(request, org_slug, event_id):
    membership, event = _manager_event(request, org_slug, event_id)
    form = PresentFilterForm(
        request.GET if request.GET else None,
        organization=membership.organization,
    )
    assignments = assignments_with_last_valid_movement(event).filter(
        latest_movement_type=Movement.Type.ENTRY,
    )
    filter_error = ''
    if form.is_bound:
        if form.is_valid():
            assignments = _apply_present_filters(assignments, form.cleaned_data)
        else:
            filter_error = 'Confira os filtros selecionados.'
    assignments = assignments.order_by('staff_member__full_name', 'pk')
    page_obj = Paginator(assignments, 50).get_page(request.GET.get('page'))
    response = render(
        request,
        'reports/present_list.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'form': form,
            'filter_error': filter_error,
            'page_obj': page_obj,
            'previous_url': (
                _query_url(request, 'reports:present_list', org_slug, event.pk, page=page_obj.previous_page_number())
                if page_obj.has_previous()
                else None
            ),
            'next_url': (
                _query_url(request, 'reports:present_list', org_slug, event.pk, page=page_obj.next_page_number())
                if page_obj.has_next()
                else None
            ),
        },
    )
    return _private_response(response)


def _apply_history_filters(movements, cleaned_data):
    query = cleaned_data.get('q', '').strip()
    if query:
        movements = movements.filter(
            Q(event_assignment__staff_member__full_name__icontains=query)
            | Q(event_assignment__company__legal_name__icontains=query)
            | Q(event_assignment__company__trade_name__icontains=query)
        )
    if cleaned_data.get('company'):
        movements = movements.filter(event_assignment__company=cleaned_data['company'])
    if cleaned_data.get('category'):
        movements = movements.filter(event_assignment__staff_member__team_category=cleaned_data['category'])
    if cleaned_data.get('role'):
        movements = movements.filter(event_assignment__staff_member__staff_role=cleaned_data['role'])
    if cleaned_data.get('movement_type'):
        movements = movements.filter(movement_type=cleaned_data['movement_type'])
    if cleaned_data.get('validity') == 'valid':
        movements = movements.filter(correction__isnull=True)
    elif cleaned_data.get('validity') == 'corrected':
        movements = movements.filter(correction__isnull=False)

    date_from = cleaned_data.get('date_from')
    date_to = cleaned_data.get('date_to')
    current_tz = timezone.get_current_timezone()
    if date_from:
        start = timezone.make_aware(datetime.combine(date_from, time.min), current_tz)
        movements = movements.filter(occurred_at__gte=start)
    if date_to:
        end_exclusive = timezone.make_aware(
            datetime.combine(date_to + timedelta(days=1), time.min),
            current_tz,
        )
        movements = movements.filter(occurred_at__lt=end_exclusive)
    return movements


def _query_url(request, route_name, org_slug, event_id, *, page=None, omit_page=False):
    params = request.GET.copy()
    if omit_page:
        params.pop('page', None)
    if page is not None:
        params['page'] = page
    base_url = reverse(route_name, args=[org_slug, event_id])
    return f'{base_url}?{params.urlencode()}' if params else base_url


@login_required
def movement_history(request, org_slug, event_id):
    membership, event = _manager_event(request, org_slug, event_id)
    form = MovementHistoryFilterForm(
        request.GET if request.GET else None,
        organization=membership.organization,
    )
    movements = movement_history_for_event(event)
    filter_error = ''
    if form.is_bound:
        if form.is_valid():
            movements = _apply_history_filters(movements, form.cleaned_data)
        else:
            filter_error = 'Confira os filtros; o período final deve ser posterior ao inicial.'
    movements = movements.order_by('-recorded_at', '-pk')
    page_obj = Paginator(movements, 50).get_page(request.GET.get('page'))
    for movement in page_obj.object_list:
        correction = getattr(movement, 'correction', None)
        movement.is_valid = correction is None
        movement.can_correct = (
            correction is None
            and movement.latest_valid_movement_id == movement.pk
        )
        movement.recorded_by_label = _user_label(movement.recorded_by)
        movement.correction_reason = correction.reason if correction else ''
        movement.corrected_by_label = _user_label(correction.corrected_by) if correction else ''
        movement.corrected_at_label = _date_label(correction.corrected_at) if correction else ''

    response = render(
        request,
        'reports/movement_history.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'form': form,
            'filter_error': filter_error,
            'page_obj': page_obj,
            'csv_url': _query_url(
                request,
                'reports:movement_csv',
                org_slug,
                event.pk,
                omit_page=True,
            ),
            'previous_url': (
                _query_url(request, 'reports:history', org_slug, event.pk, page=page_obj.previous_page_number())
                if page_obj.has_previous()
                else None
            ),
            'next_url': (
                _query_url(request, 'reports:history', org_slug, event.pk, page=page_obj.next_page_number())
                if page_obj.has_next()
                else None
            ),
        },
    )
    return _private_response(response)


def _csv_safe(value):
    text = '' if value is None else str(value)
    if text.lstrip(' \t\r\n').startswith(('=', '+', '-', '@')):
        return f"'{text}"
    return text


def _date_label(value):
    if value is None:
        return ''
    return timezone.localtime(value).strftime('%d/%m/%Y %H:%M:%S')


def _user_label(user):
    if user is None:
        return ''
    return ' '.join(part for part in (user.first_name, user.last_name) if part).strip() or f'Usuário #{user.pk}'


@login_required
def movement_csv(request, org_slug, event_id):
    membership, event = _manager_event(request, org_slug, event_id)
    form = MovementHistoryFilterForm(
        request.GET if request.GET else None,
        organization=membership.organization,
    )
    if form.is_bound and not form.is_valid():
        return _private_response(HttpResponseBadRequest('Filtros inválidos.'))
    movements = movement_history_for_event(event)
    if form.is_bound:
        movements = _apply_history_filters(movements, form.cleaned_data)
    movements = movements.order_by('-recorded_at', '-pk')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response.write('\ufeff')
    response['Content-Disposition'] = f'attachment; filename="crewpass-event-{event.pk}-movimentacoes.csv"'
    writer = csv.writer(response, delimiter=';', lineterminator='\r\n')
    writer.writerow([
        'Evento',
        'Profissional',
        'Empresa',
        'Categoria',
        'Função',
        'Movimentação',
        'Ocorrida em',
        'Registrada em',
        'Registrada por',
        'Situação',
        'Correção registrada por',
        'Corrigida em',
    ])
    for movement in movements.iterator(chunk_size=500):
        correction = getattr(movement, 'correction', None)
        assignment = movement.event_assignment
        writer.writerow([
            _csv_safe(event.name),
            _csv_safe(assignment.staff_member.full_name),
            _csv_safe(str(assignment.company) if assignment.company_id else ''),
            _csv_safe(assignment.staff_member.team_category.name),
            _csv_safe(assignment.staff_member.staff_role.name),
            _csv_safe(movement.get_movement_type_display()),
            _csv_safe(_date_label(movement.occurred_at)),
            _csv_safe(_date_label(movement.recorded_at)),
            _csv_safe(_user_label(movement.recorded_by)),
            _csv_safe('Invalidada' if correction else 'Válida'),
            _csv_safe(_user_label(correction.corrected_by) if correction else ''),
            _csv_safe(_date_label(correction.corrected_at) if correction else ''),
        ])
    return _private_response(response)
