import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from credentials.models import Credential
from events.models import Event
from organizations.models import OrganizationMembership
from staff.models import EventAssignment


class EventOperatorGrant(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.PROTECT,
        related_name='operator_grants',
        verbose_name='evento',
    )
    membership = models.ForeignKey(
        OrganizationMembership,
        on_delete=models.PROTECT,
        related_name='event_operator_grants',
        verbose_name='vínculo do operador',
    )
    is_active = models.BooleanField('ativo', default=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='event_operator_grants_given',
        verbose_name='concedido por',
    )
    granted_at = models.DateTimeField('concedido em', default=timezone.now)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='event_operator_revocations_given',
        verbose_name='revogado por',
        blank=True,
        null=True,
    )
    revoked_at = models.DateTimeField('revogado em', blank=True, null=True)

    class Meta:
        ordering = ['membership__user__email', '-granted_at']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'membership'],
                condition=Q(is_active=True),
                name='active_operator_event_grant',
            ),
        ]
        indexes = [
            models.Index(
                fields=['event', 'is_active'],
                name='opgrant_event_active_idx',
            ),
            models.Index(
                fields=['membership', 'is_active'],
                name='opgrant_member_active_idx',
            ),
        ]
        verbose_name = 'autorização de operador no evento'
        verbose_name_plural = 'autorizações de operadores nos eventos'

    def clean(self):
        super().clean()
        if self.event_id and self.membership_id:
            if self.event.organization_id != self.membership.organization_id:
                raise ValidationError(
                    'Evento e associação do operador devem pertencer à mesma organização.'
                )
            if self.membership.role != OrganizationMembership.Role.OPERATOR:
                raise ValidationError('Somente operadores podem receber acesso ao evento.')
        if self.is_active and (self.revoked_by_id or self.revoked_at):
            raise ValidationError('Uma autorização ativa não pode ter dados de revogação.')
        if not self.is_active and (not self.revoked_by_id or not self.revoked_at):
            raise ValidationError('A revogação precisa registrar usuário e data/hora.')

    def __str__(self):
        return f'{self.membership.user} — {self.event}'


class Movement(models.Model):
    class Type(models.TextChoices):
        ENTRY = 'ENTRY', 'Entrada'
        EXIT = 'EXIT', 'Saída'

    request_id = models.UUIDField('identificador da confirmação', unique=True, default=uuid.uuid4)
    event = models.ForeignKey(
        Event,
        on_delete=models.PROTECT,
        related_name='movements',
        verbose_name='evento',
    )
    event_assignment = models.ForeignKey(
        EventAssignment,
        on_delete=models.PROTECT,
        related_name='access_movements',
        verbose_name='participação',
    )
    credential = models.ForeignKey(
        Credential,
        on_delete=models.PROTECT,
        related_name='access_movements',
        verbose_name='credencial',
    )
    movement_type = models.CharField(
        'movimentação',
        max_length=5,
        choices=Type.choices,
    )
    occurred_at = models.DateTimeField('ocorrida em', default=timezone.now)
    recorded_at = models.DateTimeField('registrada em', auto_now_add=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_access_movements',
        verbose_name='registrada por',
    )

    class Meta:
        ordering = ['-recorded_at', '-pk']
        indexes = [
            models.Index(fields=['event', 'recorded_at'], name='movement_event_time_idx'),
            models.Index(
                fields=['event_assignment', 'recorded_at'],
                name='movement_assignment_time_idx',
            ),
            models.Index(fields=['credential', 'recorded_at'], name='movement_cred_time_idx'),
        ]
        verbose_name = 'movimentação de acesso'
        verbose_name_plural = 'movimentações de acesso'

    def clean(self):
        super().clean()
        if self.event_id and self.event_assignment_id and self.credential_id:
            if self.event_assignment.event_id != self.event_id:
                raise ValidationError('A participação não pertence ao evento informado.')
            if self.credential.event_assignment_id != self.event_assignment_id:
                raise ValidationError('A credencial não pertence à participação informada.')

    def __str__(self):
        return f'{self.get_movement_type_display()} — {self.credential}'


class MovementCorrection(models.Model):
    movement = models.OneToOneField(
        Movement,
        on_delete=models.PROTECT,
        related_name='correction',
        verbose_name='movimentação original',
    )
    reason = models.TextField('justificativa', max_length=500)
    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movement_corrections',
        verbose_name='corrigida por',
    )
    corrected_at = models.DateTimeField('corrigida em', auto_now_add=True)

    class Meta:
        ordering = ['-corrected_at', '-pk']
        verbose_name = 'correção de movimentação'
        verbose_name_plural = 'correções de movimentações'

    def clean(self):
        super().clean()
        if len(self.reason.strip()) < 10:
            raise ValidationError({'reason': 'A justificativa deve ter pelo menos 10 caracteres.'})

    def __str__(self):
        return f'Correção da movimentação {self.movement_id}'
