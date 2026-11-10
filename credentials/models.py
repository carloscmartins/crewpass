from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from staff.models import EventAssignment


class Credential(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Ativa'
        CANCELLED = 'CANCELLED', 'Cancelada'
        REPLACED = 'REPLACED', 'Substituída'

    event_assignment = models.ForeignKey(
        EventAssignment,
        on_delete=models.PROTECT,
        related_name='credentials',
        verbose_name='participação no evento',
    )
    code = models.CharField('código público', max_length=64, unique=True, editable=False)
    status = models.CharField(
        'status',
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    issued_at = models.DateTimeField('emitida em', default=timezone.now)
    cancelled_at = models.DateTimeField('encerrada em', blank=True, null=True)
    replaced_by = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        related_name='replaces',
        verbose_name='substituída pela credencial',
        blank=True,
        null=True,
        editable=False,
    )
    created_at = models.DateTimeField('criada em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizada em', auto_now=True)

    class Meta:
        ordering = ['-issued_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['event_assignment'],
                condition=Q(status='ACTIVE'),
                name='unique_active_credential_per_assignment',
            ),
        ]
        indexes = [
            models.Index(
                fields=['event_assignment', 'status'],
                name='cred_assign_status_idx',
            ),
        ]
        verbose_name = 'credencial'
        verbose_name_plural = 'credenciais'

    def clean(self):
        super().clean()
        if self.status == self.Status.ACTIVE:
            if self.cancelled_at or self.replaced_by_id:
                raise ValidationError(
                    'Uma credencial ativa não pode estar cancelada ou substituída.'
                )
        elif self.status == self.Status.CANCELLED:
            if not self.cancelled_at or self.replaced_by_id:
                raise ValidationError(
                    'Credencial cancelada precisa de data de cancelamento '
                    'e não pode ter substituta.'
                )
        elif self.status == self.Status.REPLACED:
            if not self.cancelled_at or not self.replaced_by_id:
                raise ValidationError(
                    'Credencial substituída precisa de data e referência à nova credencial.'
                )
            if self.replaced_by.event_assignment_id != self.event_assignment_id:
                raise ValidationError(
                    'A substituta deve pertencer à mesma participação no evento.'
                )

    def __str__(self):
        identifier = self.pk if self.pk else 'nova'
        return f'Credencial {identifier} — {self.get_status_display()}'


class CredentialAuditLog(models.Model):
    class Action(models.TextChoices):
        ISSUED = 'ISSUED', 'Emitida'
        CANCELLED = 'CANCELLED', 'Cancelada'
        REPLACED = 'REPLACED', 'Substituída'

    credential = models.ForeignKey(
        Credential,
        on_delete=models.PROTECT,
        related_name='audit_entries',
        verbose_name='credencial',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='credential_actions',
        verbose_name='usuário responsável',
    )
    action = models.CharField('ação', max_length=12, choices=Action.choices)
    replacement = models.ForeignKey(
        Credential,
        on_delete=models.PROTECT,
        related_name='replacement_audit_entries',
        verbose_name='credencial substituta',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField('registrada em', auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'registro de auditoria de credencial'
        verbose_name_plural = 'registros de auditoria de credenciais'

    def clean(self):
        super().clean()
        if self.action == self.Action.REPLACED:
            if not self.replacement_id:
                raise ValidationError(
                    'O registro de substituição deve referenciar a nova credencial.'
                )
            if self.replacement.event_assignment_id != self.credential.event_assignment_id:
                raise ValidationError(
                    'A substituta deve pertencer à mesma participação no evento.'
                )
        elif self.replacement_id:
            raise ValidationError(
                'Somente uma substituição pode referenciar uma nova credencial.'
            )

    def __str__(self):
        return f'{self.get_action_display()} — {self.credential}'
