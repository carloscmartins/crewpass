from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from credentials.models import Credential
from organizations.access import get_membership, require_manager
from staff.models import EventAssignment

from .forms import EventForm
from .models import Event


@login_required
def event_list(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    events = Event.objects.filter(organization=membership.organization)
    query = request.GET.get('q', '').strip()
    selected_status = request.GET.get('status', '')
    if query:
        events = events.filter(Q(name__icontains=query) | Q(location__icontains=query))
    if selected_status in Event.Status.values:
        events = events.filter(status=selected_status)
    return render(
        request,
        'events/event_list.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'events': events,
            'query': query,
            'selected_status': selected_status,
            'status_choices': Event.Status.choices,
        },
    )


@login_required
def event_detail(request, org_slug, pk):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = get_object_or_404(Event, organization=membership.organization, pk=pk)
    active_assignments = EventAssignment.objects.filter(
        organization=membership.organization,
        event=event,
        status=EventAssignment.Status.ACTIVE,
        staff_member__is_active=True,
    )
    active_assignment_count = active_assignments.count()
    active_credential_count = Credential.objects.filter(
        event_assignment__in=active_assignments,
        status=Credential.Status.ACTIVE,
    ).count()
    return render(
        request,
        'events/event_detail.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'event': event,
            'active_assignment_count': active_assignment_count,
            'active_credential_count': active_credential_count,
            'missing_credential_count': max(
                active_assignment_count - active_credential_count,
                0,
            ),
        },
    )


@login_required
def event_create(request, org_slug):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    return _event_form(request, membership, None)


@login_required
def event_edit(request, org_slug, pk):
    membership = get_membership(request, org_slug)
    require_manager(membership)
    event = get_object_or_404(Event, organization=membership.organization, pk=pk)
    return _event_form(request, membership, event)


def _event_form(request, membership, event):
    form = EventForm(request.POST if request.method == 'POST' else None, instance=event)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.organization = membership.organization
        event.save()
        messages.success(request, 'Evento salvo com sucesso.')
        return redirect('events:detail', org_slug=membership.organization.slug, pk=event.pk)

    return render(
        request,
        'crud/form.html',
        {
            'organization': membership.organization,
            'membership': membership,
            'form': form,
            'page_title': 'Editar evento' if event else 'Novo evento',
            'page_description': 'Informe os dados e o período de realização.',
            'cancel_url': reverse(
                'events:detail' if event else 'events:list',
                kwargs=(
                    {'org_slug': membership.organization.slug, 'pk': event.pk}
                    if event
                    else {'org_slug': membership.organization.slug}
                ),
            ),
        },
    )
