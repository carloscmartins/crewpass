from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from events.models import Event
from organizations.access import get_membership, require_manager
from staff.models import EventAssignment

from .forms import ConfirmCredentialActionForm
from .models import Credential
from .qr import qr_svg_data
from .services import cancel_credential, issue_credential, replace_credential


def _get_event(membership, event_id):
    return get_object_or_404(
        Event,
        organization=membership.organization,
        pk=event_id,
    )


def _get_credential(membership, event, credential_id):
    return get_object_or_404(
        Credential.objects.select_related(
            'event_assignment__staff_member',
            'event_assignment__event',
            'event_assignment__company',
            'event_assignment__staff_member__team_category',
            'event_assignment__staff_member__staff_role',
            'replaced_by',
        ),
        event_assignment__organization=membership.organization,
        event_assignment__event=event,
        pk=credential_id,
    )


@login_required
def credential_list(request, org_slug, event_id):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = _get_event(membership, event_id)
    assignments = EventAssignment.objects.filter(
        organization=membership.organization,
        event=event,
    ).select_related('staff_member', 'company', 'staff_member__team_category', 'staff_member__staff_role')
    query = request.GET.get('q', '').strip()
    if query:
        assignments = assignments.filter(
            Q(staff_member__full_name__icontains=query)
            | Q(company__legal_name__icontains=query)
            | Q(company__trade_name__icontains=query)
        )

    assignment_ids = list(assignments.values_list('pk', flat=True))
    credentials = Credential.objects.filter(
        event_assignment_id__in=assignment_ids,
    ).order_by('issued_at', 'pk')
    latest_by_assignment = {}
    active_by_assignment = {}
    for credential in credentials:
        latest_by_assignment[credential.event_assignment_id] = credential
        if credential.status == Credential.Status.ACTIVE:
            active_by_assignment[credential.event_assignment_id] = credential

    rows = [
        {
            'assignment': assignment,
            'credential': active_by_assignment.get(assignment.pk)
            or latest_by_assignment.get(assignment.pk),
            'active_credential': active_by_assignment.get(assignment.pk),
            'eligible': (
                assignment.status == EventAssignment.Status.ACTIVE
                and event.status != Event.Status.CANCELLED
            ),
        }
        for assignment in assignments
    ]
    return render(
        request,
        'credentials/credential_list.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'rows': rows,
            'query': query,
        },
    )


@login_required
def credential_issue(request, org_slug, event_id, assignment_id):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = _get_event(membership, event_id)
    assignment = get_object_or_404(
        EventAssignment.objects.select_related('staff_member', 'event'),
        organization=membership.organization,
        event=event,
        pk=assignment_id,
    )
    existing = Credential.objects.filter(
        event_assignment=assignment,
        status=Credential.Status.ACTIVE,
    ).first()
    if existing:
        messages.info(request, 'Esta participação já possui uma credencial ativa.')
        return redirect(
            'credentials:list',
            org_slug=org_slug,
            event_id=event.pk,
        )

    form = ConfirmCredentialActionForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            issue_credential(assignment, actor=request.user)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Credencial emitida com sucesso.')
            return redirect(
                'credentials:list',
                org_slug=org_slug,
                event_id=event.pk,
            )

    return render(
        request,
        'credentials/confirm_action.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'assignment': assignment,
            'credential': None,
            'form': form,
            'action_title': 'Emitir credencial',
            'action_description': (
                'Será criado um código público aleatório para esta participação. '
                'O QR Code não inclui dados pessoais.'
            ),
            'submit_label': 'Emitir credencial',
            'cancel_url': reverse('credentials:list', args=[org_slug, event.pk]),
        },
    )


@login_required
def credential_action(request, org_slug, event_id, credential_id, action):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = _get_event(membership, event_id)
    if action not in ('cancel', 'replace'):
        raise Http404

    credential = _get_credential(membership, event, credential_id)
    if credential.status != Credential.Status.ACTIVE:
        messages.error(request, 'A credencial selecionada não está ativa.')
        return redirect('credentials:list', org_slug=org_slug, event_id=event.pk)

    form = ConfirmCredentialActionForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            if action == 'cancel':
                cancel_credential(credential, actor=request.user)
                messages.success(
                    request,
                    'Credencial cancelada. O código anterior não pode ser reutilizado.',
                )
            else:
                replace_credential(credential, actor=request.user)
                messages.success(
                    request,
                    'Credencial substituída; a nova credencial já está ativa.',
                )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect('credentials:list', org_slug=org_slug, event_id=event.pk)

    return render(
        request,
        'credentials/confirm_action.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'assignment': credential.event_assignment,
            'credential': credential,
            'form': form,
            'action_title': (
                'Cancelar credencial' if action == 'cancel' else 'Substituir credencial'
            ),
            'action_description': (
                'O código atual deixará de ser válido. '
                'Esta ação não pode ser desfeita.'
                if action == 'cancel'
                else (
                    'O código atual deixará de ser válido e uma nova credencial '
                    'será emitida.'
                )
            ),
            'submit_label': (
                'Confirmar cancelamento' if action == 'cancel' else 'Confirmar substituição'
            ),
            'cancel_url': reverse('credentials:list', args=[org_slug, event.pk]),
        },
    )


@login_required
def credential_print(request, org_slug, event_id, credential_id):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = _get_event(membership, event_id)
    credential = _get_credential(membership, event, credential_id)
    if credential.status != Credential.Status.ACTIVE:
        messages.error(request, 'Somente credenciais ativas podem ser impressas.')
        return redirect('credentials:list', org_slug=org_slug, event_id=event.pk)
    if (
        credential.event_assignment.status != EventAssignment.Status.ACTIVE
        or event.status == Event.Status.CANCELLED
    ):
        messages.error(
            request,
            'A participação ou o evento está cancelado; '
            'não é possível imprimir a credencial.',
        )
        return redirect('credentials:list', org_slug=org_slug, event_id=event.pk)

    return render(
        request,
        'credentials/credential_print.html',
        {
            'organization': membership.organization,
            'event': event,
            'credential': credential,
            'qr_image': qr_svg_data(credential.code),
        },
    )
