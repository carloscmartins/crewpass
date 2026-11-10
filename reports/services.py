from datetime import timedelta

from django.db.models import OuterRef, Q, Subquery
from django.utils import timezone

from access_control.models import Movement
from events.models import Event
from staff.models import EventAssignment


def credentialed_assignments(event):
    organization_id = event.organization_id
    return EventAssignment.objects.filter(
        organization_id=organization_id,
        event=event,
        credentials__isnull=False,
        staff_member__organization_id=organization_id,
    ).filter(
        Q(company__isnull=True) | Q(company__organization_id=organization_id)
    ).select_related(
        'staff_member', 'company', 'staff_member__team_category', 'staff_member__staff_role'
    ).distinct()


def assignments_with_last_valid_movement(event):
    latest_valid = Movement.objects.filter(
        event=event,
        event_assignment_id=OuterRef('pk'),
        correction__isnull=True,
    ).order_by('-recorded_at', '-pk')
    return credentialed_assignments(event).annotate(
        latest_movement_id=Subquery(latest_valid.values('pk')[:1]),
        latest_movement_type=Subquery(latest_valid.values('movement_type')[:1]),
        latest_movement_at=Subquery(latest_valid.values('recorded_at')[:1]),
    )


def event_movements(event):
    organization_id = event.organization_id
    return Movement.objects.filter(
        event=event,
        event_assignment__event=event,
        event_assignment__organization_id=organization_id,
        event_assignment__staff_member__organization_id=organization_id,
    ).filter(
        Q(event_assignment__company__isnull=True)
        | Q(event_assignment__company__organization_id=organization_id)
    ).select_related(
        'event',
        'event_assignment__staff_member',
        'event_assignment__company',
        'event_assignment__staff_member__team_category',
        'event_assignment__staff_member__staff_role',
        'recorded_by',
        'correction__corrected_by',
    )


def presence_periods_for_event(event, as_of=None):
    """Return valid entry/exit pairs and their summed estimated presence time."""
    as_of = as_of or timezone.now()
    total = timedelta()
    open_entries = {}
    periods = []
    movements = event_movements(event).filter(
        correction__isnull=True,
    ).order_by(
        'event_assignment_id', 'recorded_at', 'pk'
    )

    for movement in movements:
        assignment_id = movement.event_assignment_id
        if movement.movement_type == Movement.Type.ENTRY:
            open_entries[assignment_id] = movement
            continue

        entry_at = open_entries.pop(assignment_id, None)
        if entry_at is None:
            continue
        duration = max(movement.occurred_at - entry_at.occurred_at, timedelta())
        total += duration
        periods.append({
            'assignment': movement.event_assignment,
            'entry_at': entry_at.occurred_at,
            'exit_at': movement.occurred_at,
            'sort_at': movement.recorded_at,
        })

    for entry in open_entries.values():
        duration = max(as_of - entry.occurred_at, timedelta())
        total += duration
        periods.append({
            'assignment': entry.event_assignment,
            'entry_at': entry.occurred_at,
            'exit_at': None,
            'sort_at': entry.recorded_at,
        })

    periods.sort(key=lambda period: period['sort_at'], reverse=True)
    return periods, total


def movement_history_for_event(event):
    latest_valid = Movement.objects.filter(
        event=event,
        event_assignment_id=OuterRef('event_assignment_id'),
        correction__isnull=True,
    ).order_by('-recorded_at', '-pk')
    return event_movements(event).annotate(
        latest_valid_movement_id=Subquery(latest_valid.values('pk')[:1]),
    )
