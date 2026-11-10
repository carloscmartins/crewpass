import secrets

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from events.models import Event
from staff.models import EventAssignment

from .models import Credential, CredentialAuditLog


def _new_code():
    return secrets.token_urlsafe(32)


@transaction.atomic
def issue_credential(event_assignment, actor):
    assignment = EventAssignment.objects.select_for_update().select_related('event').get(
        pk=event_assignment.pk
    )
    if assignment.status != EventAssignment.Status.ACTIVE:
        raise ValidationError('Não é possível emitir credencial para participação cancelada.')
    if assignment.event.status == Event.Status.CANCELLED:
        raise ValidationError('Não é possível emitir credencial para evento cancelado.')
    if Credential.objects.filter(
        event_assignment=assignment,
        status=Credential.Status.ACTIVE,
    ).exists():
        raise ValidationError('Esta participação já possui uma credencial ativa.')

    credential = Credential.objects.create(
        event_assignment=assignment,
        code=_new_code(),
        status=Credential.Status.ACTIVE,
    )
    CredentialAuditLog.objects.create(
        credential=credential,
        actor=actor,
        action=CredentialAuditLog.Action.ISSUED,
    )
    return credential


@transaction.atomic
def cancel_credential(credential, actor):
    EventAssignment.objects.select_for_update().get(pk=credential.event_assignment_id)
    current = Credential.objects.select_for_update().get(pk=credential.pk)
    if current.status != Credential.Status.ACTIVE:
        raise ValidationError('Somente uma credencial ativa pode ser cancelada.')

    current.status = Credential.Status.CANCELLED
    current.cancelled_at = timezone.now()
    current.save(update_fields=['status', 'cancelled_at', 'updated_at'])
    CredentialAuditLog.objects.create(
        credential=current,
        actor=actor,
        action=CredentialAuditLog.Action.CANCELLED,
    )
    return current


@transaction.atomic
def replace_credential(credential, actor):
    assignment = EventAssignment.objects.select_for_update().select_related('event').get(
        pk=credential.event_assignment_id
    )
    current = Credential.objects.select_for_update().get(pk=credential.pk)
    if current.status != Credential.Status.ACTIVE:
        raise ValidationError('Somente uma credencial ativa pode ser substituída.')
    if assignment.status != EventAssignment.Status.ACTIVE:
        raise ValidationError(
            'Não é possível substituir credencial de participação cancelada.'
        )
    if assignment.event.status == Event.Status.CANCELLED:
        raise ValidationError('Não é possível substituir credencial de evento cancelado.')

    now = timezone.now()
    current.status = Credential.Status.REPLACED
    current.cancelled_at = now
    current.save(update_fields=['status', 'cancelled_at', 'updated_at'])

    replacement = Credential.objects.create(
        event_assignment=assignment,
        code=_new_code(),
        status=Credential.Status.ACTIVE,
        issued_at=now,
    )
    current.replaced_by = replacement
    current.save(update_fields=['replaced_by', 'updated_at'])
    CredentialAuditLog.objects.create(
        credential=current,
        actor=actor,
        action=CredentialAuditLog.Action.REPLACED,
        replacement=replacement,
    )
    return replacement
