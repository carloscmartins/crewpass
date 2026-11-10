from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from events.models import Event
from organizations.access import MANAGER_ROLES, get_membership
from organizations.models import OrganizationMembership

from .models import EventOperatorGrant


def require_active_user(request):
    if not request.user.is_active:
        raise PermissionDenied('Sua conta não está ativa.')


def get_event_access(request, org_slug, event_id, *, active_only=True):
    require_active_user(request)
    membership = get_membership(request, org_slug)
    event = get_object_or_404(
        Event,
        organization=membership.organization,
        pk=event_id,
    )
    if active_only and event.status != Event.Status.ACTIVE:
        raise PermissionDenied('A operação está disponível somente para eventos ativos.')
    if membership.role not in MANAGER_ROLES:
        if membership.role != OrganizationMembership.Role.OPERATOR:
            raise PermissionDenied('Seu perfil não pode operar este evento.')
        allowed = EventOperatorGrant.objects.filter(
            event=event,
            membership=membership,
            is_active=True,
        ).exists()
        if not allowed:
            raise PermissionDenied('Você não está autorizado a operar este evento.')
    return membership, event
