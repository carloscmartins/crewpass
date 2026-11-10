from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import OrganizationMembership


MANAGER_ROLES = {
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.SUPERVISOR,
}


def get_membership(request, organization_slug):
    return get_object_or_404(
        OrganizationMembership.objects.select_related('organization'),
        organization__slug=organization_slug,
        organization__is_active=True,
        user=request.user,
        is_active=True,
    )


def require_manager(membership):
    if membership.role not in MANAGER_ROLES:
        raise PermissionDenied('Seu perfil não pode gerenciar os cadastros desta organização.')
