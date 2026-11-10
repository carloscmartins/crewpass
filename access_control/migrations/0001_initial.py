import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('credentials', '0002_credentialauditlog'),
        ('events', '0001_initial'),
        ('organizations', '0001_initial'),
        ('staff', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EventOperatorGrant',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('is_active', models.BooleanField(default=True, verbose_name='ativo')),
                (
                    'granted_at',
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name='concedido em'),
                ),
                ('revoked_at', models.DateTimeField(blank=True, null=True, verbose_name='revogado em')),
                (
                    'event',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='operator_grants',
                        to='events.event',
                        verbose_name='evento',
                    ),
                ),
                (
                    'granted_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='event_operator_grants_given',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='concedido por',
                    ),
                ),
                (
                    'membership',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='event_operator_grants',
                        to='organizations.organizationmembership',
                        verbose_name='vínculo do operador',
                    ),
                ),
                (
                    'revoked_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='event_operator_revocations_given',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='revogado por',
                    ),
                ),
            ],
            options={
                'verbose_name': 'autorização de operador no evento',
                'verbose_name_plural': 'autorizações de operadores nos eventos',
                'ordering': ['membership__user__email', '-granted_at'],
                'indexes': [
                    models.Index(fields=['event', 'is_active'], name='opgrant_event_active_idx'),
                    models.Index(fields=['membership', 'is_active'], name='opgrant_member_active_idx'),
                ],
                'constraints': [
                    models.UniqueConstraint(
                        condition=Q(('is_active', True)),
                        fields=('event', 'membership'),
                        name='active_operator_event_grant',
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name='Movement',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'request_id',
                    models.UUIDField(
                        default=uuid.uuid4,
                        unique=True,
                        verbose_name='identificador da confirmação',
                    ),
                ),
                (
                    'movement_type',
                    models.CharField(
                        choices=[('ENTRY', 'Entrada'), ('EXIT', 'Saída')],
                        max_length=5,
                        verbose_name='movimentação',
                    ),
                ),
                (
                    'occurred_at',
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name='ocorrida em'),
                ),
                (
                    'recorded_at',
                    models.DateTimeField(auto_now_add=True, verbose_name='registrada em'),
                ),
                (
                    'credential',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='access_movements',
                        to='credentials.credential',
                        verbose_name='credencial',
                    ),
                ),
                (
                    'event',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='movements',
                        to='events.event',
                        verbose_name='evento',
                    ),
                ),
                (
                    'event_assignment',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='access_movements',
                        to='staff.eventassignment',
                        verbose_name='participação',
                    ),
                ),
                (
                    'recorded_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='recorded_access_movements',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='registrada por',
                    ),
                ),
            ],
            options={
                'verbose_name': 'movimentação de acesso',
                'verbose_name_plural': 'movimentações de acesso',
                'ordering': ['-recorded_at', '-pk'],
                'indexes': [
                    models.Index(fields=['event', 'recorded_at'], name='movement_event_time_idx'),
                    models.Index(
                        fields=['event_assignment', 'recorded_at'],
                        name='movement_assignment_time_idx',
                    ),
                    models.Index(fields=['credential', 'recorded_at'], name='movement_cred_time_idx'),
                ],
            },
        ),
    ]
