from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Organization, OrganizationMembership


@login_required
def dashboard(request):
    memberships = OrganizationMembership.objects.filter(
        user=request.user,
        is_active=True,
        organization__is_active=True,
    ).select_related('organization')
    return render(request, 'organizations/dashboard.html', {'memberships': memberships})


@login_required
def organization_detail(request, slug):
    organization = get_object_or_404(
        Organization.objects.filter(
            memberships__user=request.user,
            memberships__is_active=True,
            is_active=True,
        ),
        slug=slug,
    )
    membership = get_object_or_404(
        OrganizationMembership,
        organization=organization,
        user=request.user,
        is_active=True,
    )
    return render(
        request,
        'organizations/detail.html',
        {'organization': organization, 'membership': membership},
    )
