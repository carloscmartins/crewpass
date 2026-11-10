from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from events.models import Event
from organizations.models import Organization


class Company(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='companies',
        verbose_name='organização',
    )
    legal_name = models.CharField('razão social ou nome', max_length=200)
    trade_name = models.CharField('nome fantasia', max_length=200, blank=True)
    document = models.CharField('CNPJ', max_length=18, blank=True)
    contact_name = models.CharField('contato responsável', max_length=150, blank=True)
    phone = models.CharField('telefone', max_length=30, blank=True)
    email = models.EmailField('e-mail', blank=True)
    is_active = models.BooleanField('ativa', default=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizada em', auto_now=True)

    class Meta:
        ordering = ['legal_name']
        indexes = [
            models.Index(fields=['organization', 'is_active'], name='company_org_active_idx'),
        ]
        verbose_name = 'empresa'
        verbose_name_plural = 'empresas'

    def __str__(self):
        return self.trade_name or self.legal_name


class StaffMember(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='staff_members',
        verbose_name='organização',
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='staff_members',
        verbose_name='empresa',
        blank=True,
        null=True,
    )
    full_name = models.CharField('nome completo', max_length=180)
    document = models.CharField(
        'CPF (opcional)',
        max_length=14,
        blank=True,
        help_text='Informe apenas se necessário para a operação.',
    )
    phone = models.CharField('telefone', max_length=30, blank=True)
    email = models.EmailField('e-mail', blank=True)
    team_category = models.ForeignKey(
        'TeamCategory',
        on_delete=models.PROTECT,
        related_name='staff_members',
        verbose_name='categoria',
        blank=True,
        null=True,
    )
    staff_role = models.ForeignKey(
        'StaffRole',
        on_delete=models.PROTECT,
        related_name='staff_members',
        verbose_name='função',
        blank=True,
        null=True,
    )
    notes = models.TextField('observações operacionais', blank=True)
    is_active = models.BooleanField('ativo', default=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['full_name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'document'],
                condition=~Q(document=''),
                name='unique_staff_document_per_org',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'is_active'], name='staff_org_active_idx'),
        ]
        verbose_name = 'profissional'
        verbose_name_plural = 'profissionais'

    def __str__(self):
        return self.full_name


class TeamCategory(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='team_categories',
        verbose_name='organização',
    )
    name = models.CharField('nome', max_length=100)
    is_active = models.BooleanField('ativa', default=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizada em', auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_category_per_org',
            ),
        ]
        verbose_name = 'categoria de equipe'
        verbose_name_plural = 'categorias de equipe'

    def __str__(self):
        return self.name


class StaffRole(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='staff_roles',
        verbose_name='organização',
    )
    team_category = models.ForeignKey(
        TeamCategory,
        on_delete=models.PROTECT,
        related_name='staff_roles',
        verbose_name='categoria',
        blank=True,
        null=True,
    )
    name = models.CharField('nome', max_length=120)
    is_active = models.BooleanField('ativa', default=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizada em', auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'team_category', 'name'],
                condition=Q(team_category__isnull=False),
                name='unique_role_per_category',
            ),
        ]
        verbose_name = 'função'
        verbose_name_plural = 'funções'

    def clean(self):
        super().clean()
        if self.team_category_id and self.organization_id:
            if self.team_category.organization_id != self.organization_id:
                raise ValidationError('A função e a categoria devem pertencer à mesma organização.')

    def __str__(self):
        if self.team_category_id:
            return f'{self.team_category.name} — {self.name}'
        return self.name


class Shift(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name='organização',
    )
    name = models.CharField('nome', max_length=120)
    starts_at = models.TimeField('início')
    ends_at = models.TimeField('término')
    is_active = models.BooleanField('ativo', default=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_shift_name_per_org',
            ),
        ]
        verbose_name = 'turno'
        verbose_name_plural = 'turnos'

    @property
    def ends_next_day(self):
        return self.ends_at < self.starts_at

    def __str__(self):
        return f'{self.name} ({self.starts_at:%H:%M}–{self.ends_at:%H:%M})'


class EventAssignment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Ativa'
        CANCELLED = 'CANCELLED', 'Cancelada'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='event_assignments',
        verbose_name='organização',
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name='evento',
    )
    staff_member = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name='event_assignments',
        verbose_name='profissional',
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='event_assignments',
        verbose_name='empresa',
        blank=True,
        null=True,
    )
    status = models.CharField(
        'status',
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    notes = models.TextField('observações', blank=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizada em', auto_now=True)

    class Meta:
        ordering = ['event__starts_at', 'staff_member__full_name']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'staff_member'],
                name='unique_staff_assignment_per_event',
            ),
        ]
        indexes = [
            models.Index(
                fields=['organization', 'event', 'status'],
                name='assignment_event_status_idx',
            ),
        ]
        verbose_name = 'participação em evento'
        verbose_name_plural = 'participações em eventos'

    def clean(self):
        super().clean()
        related = {
            'event': self.event_id,
            'staff_member': self.staff_member_id,
        }
        if any(not value for value in related.values()):
            return

        organization_ids = {
            'event': self.event.organization_id,
            'staff_member': self.staff_member.organization_id,
        }
        if self.company_id:
            organization_ids['company'] = self.company.organization_id
        if self.staff_member_id and self.staff_member.team_category_id:
            organization_ids['team_category'] = self.staff_member.team_category.organization_id
        if self.staff_member_id and self.staff_member.staff_role_id:
            organization_ids['staff_role'] = self.staff_member.staff_role.organization_id

        if any(
            organization_id != self.organization_id
            for organization_id in organization_ids.values()
        ):
            raise ValidationError(
                'Evento, profissional e empresa devem pertencer '
                'à mesma organização.'
            )

    def __str__(self):
        return f'{self.staff_member} — {self.event}'


class EventAssignmentShift(models.Model):
    event_assignment = models.ForeignKey(
        EventAssignment,
        on_delete=models.CASCADE,
        related_name='scheduled_shifts',
        verbose_name='participação',
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='assignment_shifts',
        verbose_name='turno',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='event_assignment_shifts_created',
        verbose_name='cadastrado por',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='event_assignment_shifts_updated',
        verbose_name='atualizado por',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField('cadastrado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['shift__name']
        constraints = [
            models.UniqueConstraint(
                fields=['event_assignment'],
                name='unique_assignment_shift',
            ),
        ]
        indexes = [
            models.Index(
                fields=['event_assignment'],
                name='assign_shift_assignment_idx',
            ),
        ]
        verbose_name = 'turno da participação'
        verbose_name_plural = 'turnos das participações'

    @property
    def starts_at(self):
        return self.shift.starts_at

    @property
    def ends_at(self):
        return self.shift.ends_at

    @property
    def ends_next_day(self):
        return self.shift.ends_next_day

    def __str__(self):
        return (
            f'{self.event_assignment.staff_member} — '
            f'{self.shift.name} ({self.shift.starts_at:%H:%M}–{self.shift.ends_at:%H:%M})'
        )
