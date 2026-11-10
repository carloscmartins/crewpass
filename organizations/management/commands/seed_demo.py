from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership
from events.models import Event

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria dados de demonstração básicos.'

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(name='Organização Demo', defaults={'is_active': True})
        user, created = User.objects.get_or_create(email='demo@crewpass.local', defaults={'first_name': 'Demo', 'last_name': 'User', 'is_staff': True, 'is_active': True})
        if created:
            user.set_password('demo12345')
            user.save()
        OrganizationMembership.objects.get_or_create(organization=org, user=user, defaults={'role': OrganizationMembership.Role.ADMIN, 'is_active': True})
        now = timezone.now()
        Event.objects.get_or_create(organization=org, name='Evento Demo', defaults={
            'location': 'Local Demo',
            'starts_at': now + timedelta(days=1),
            'ends_at': now + timedelta(days=2),
            'status': Event.Status.ACTIVE,
        })
        self.stdout.write(self.style.SUCCESS('Dados demo criados.'))