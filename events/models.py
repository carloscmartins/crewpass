from django.core.exceptions import ValidationError
from django.db import models

from organizations.models import Organization


class Event(models.Model):
    class Status(models.TextChoices):
        PLANNING = 'PLANNING', 'Planejamento'
        ACTIVE = 'ACTIVE', 'Ativo'
        FINISHED = 'FINISHED', 'Encerrado'
        CANCELLED = 'CANCELLED', 'Cancelado'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='organização',
    )
    name = models.CharField('nome', max_length=180)
    description = models.TextField('descrição', blank=True)
    location = models.CharField('local', max_length=200)
    starts_at = models.DateTimeField('início')
    ends_at = models.DateTimeField('término')
    status = models.CharField(
        'status',
        max_length=16,
        choices=Status.choices,
        default=Status.PLANNING,
    )
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['-starts_at', 'name']
        indexes = [models.Index(fields=['organization', 'status'], name='event_org_status_idx')]
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({'ends_at': 'O término deve ser posterior ao início.'})

    def __str__(self):
        return self.name
