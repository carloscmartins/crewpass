import re
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q, Value
from django.db.models.functions import Replace
from django.utils import timezone

from credentials.models import Credential
from events.models import Event
from organizations.access import MANAGER_ROLES
from organizations.models import OrganizationMembership
from staff.models import EventAssignment

from .models import EventOperatorGrant, Movement, MovementCorrection


def _manager_membership(event, actor, *, lock=False):
    memberships = OrganizationMembership.objects
    if lock:
        memberships = memberships.select_for_update()
    membership = memberships.filter(
        organization_id=event.organization_id,
        user=actor,
        user__is_active=True,
        is_active=True,
    ).first()
    if membership is None or membership.role not in MANAGER_ROLES:
        raise PermissionDenied('Somente administradores e supervisores podem gerenciar o evento.')
    return membership


@transaction.atomic
def grant_event_operator(event, operator_membership, actor):
    current_event = Event.objects.select_for_update().get(
        pk=event.pk,
        organization_id=event.organization_id,
    )
    _manager_membership(current_event, actor, lock=True)
    operator = OrganizationMembership.objects.select_for_update().filter(
        pk=operator_membership.pk,
        organization_id=current_event.organization_id,
        user__is_active=True,
        is_active=True,
        role=OrganizationMembership.Role.OPERATOR,
    ).first()
    if operator is None:
        raise ValidationError('Selecione um operador ativo desta organização.')

    active_grant = EventOperatorGrant.objects.filter(
        event=current_event,
        membership=operator,
        is_active=True,
    ).first()
    if active_grant:
        return active_grant, False

    try:
        with transaction.atomic():
            grant = EventOperatorGrant.objects.create(
                event=current_event,
                membership=operator,
                granted_by=actor,
            )
    except IntegrityError:
        grant = EventOperatorGrant.objects.get(
            event=current_event,
            membership=operator,
            is_active=True,
        )
        return grant, False
    return grant, True


@transaction.atomic
def revoke_event_operator(event, grant_id, actor):
    current_event = Event.objects.select_for_update().get(
        pk=event.pk,
        organization_id=event.organization_id,
    )
    _manager_membership(current_event, actor, lock=True)
    grant = EventOperatorGrant.objects.select_for_update().filter(
        pk=grant_id,
        event=current_event,
        is_active=True,
    ).first()
    if grant is None:
        raise ValidationError('A autorização selecionada não está ativa.')
    grant.is_active = False
    grant.revoked_by = actor
    grant.revoked_at = timezone.now()
    grant.save(update_fields=['is_active', 'revoked_by', 'revoked_at'])
    return grant


def search_event_assignments(event, query):
    query = query.strip()
    if len(query) < 2:
        raise ValidationError('Digite pelo menos dois caracteres do nome ou informe o CPF completo.')

    digits = re.sub(r'\D', '', query)
    assignments = EventAssignment.objects.filter(
        organization_id=event.organization_id,
        event=event,
        status=EventAssignment.Status.ACTIVE,
        staff_member__is_active=True,
        staff_member__organization_id=event.organization_id,
        staff_member__team_category__organization_id=event.organization_id,
        staff_member__staff_role__organization_id=event.organization_id,
        credentials__status=Credential.Status.ACTIVE,
    ).filter(
        Q(company__isnull=True) | Q(company__organization_id=event.organization_id)
    ).select_related('staff_member', 'company', 'staff_member__team_category', 'staff_member__staff_role')

    if digits:
        if len(digits) != 11:
            raise ValidationError('Para busca por CPF, informe os 11 dígitos completos.')
        normalized_document = 'staff_member__document'
        for character in ('.', '-', '/', ' '):
            normalized_document = Replace(
                normalized_document,
                Value(character),
                Value(''),
            )
        assignments = assignments.annotate(
            normalized_document=normalized_document,
        ).filter(normalized_document=digits)
    else:
        assignments = assignments.filter(staff_member__full_name__icontains=query)

    return list(assignments.distinct().order_by('staff_member__full_name', 'pk')[:31])


def next_movement_type(last_movement):
    if last_movement is None or last_movement.movement_type == Movement.Type.EXIT:
        return Movement.Type.ENTRY
    return Movement.Type.EXIT


@transaction.atomic
def record_movement(
    *,
    event_id,
    organization_id,
    credential_id,
    actor,
    expected_type,
    expected_last_movement_id,
    request_id,
):
    try:
        request_id = uuid.UUID(str(request_id))
    except (TypeError, ValueError, AttributeError) as error:
        raise ValidationError('A confirmação expirou. Leia a credencial novamente.') from error

    event = Event.objects.filter(
        pk=event_id,
        organization_id=organization_id,
        status=Event.Status.ACTIVE,
        organization__is_active=True,
    ).first()
    if event is None:
        raise ValidationError('O evento não está ativo para registrar movimentações.')

    membership = OrganizationMembership.objects.select_for_update().filter(
        organization_id=organization_id,
        user=actor,
        user__is_active=True,
        is_active=True,
    ).first()
    if membership is None:
        raise PermissionDenied('Sua associação com esta organização não está ativa.')
    if membership.role not in MANAGER_ROLES:
        if membership.role != OrganizationMembership.Role.OPERATOR:
            raise PermissionDenied('Seu perfil não pode operar este evento.')
        grant = EventOperatorGrant.objects.select_for_update().filter(
            event=event,
            membership=membership,
            is_active=True,
        ).first()
        if grant is None:
            raise PermissionDenied('Você não está mais autorizado a operar este evento.')

    prior_request = Movement.objects.filter(request_id=request_id).first()
    if prior_request:
        if (
            prior_request.event_id == event.pk
            and prior_request.credential_id == credential_id
            and prior_request.recorded_by_id == actor.pk
        ):
            return prior_request, False
        raise ValidationError('Esta confirmação já foi usada para outra movimentação.')

    credential = Credential.objects.filter(
        pk=credential_id,
        event_assignment__event=event,
        event_assignment__organization_id=organization_id,
        event_assignment__status=EventAssignment.Status.ACTIVE,
        event_assignment__staff_member__is_active=True,
        event_assignment__staff_member__organization_id=organization_id,
        event_assignment__staff_member__team_category__organization_id=organization_id,
        event_assignment__staff_member__staff_role__organization_id=organization_id,
        status=Credential.Status.ACTIVE,
    ).filter(
        Q(event_assignment__company__isnull=True)
        | Q(event_assignment__company__organization_id=organization_id)
    ).first()
    if credential is None:
        raise ValidationError('A credencial não está ativa para este evento.')

    assignment = EventAssignment.objects.select_for_update().filter(
        pk=credential.event_assignment_id,
        event=event,
        organization_id=organization_id,
        status=EventAssignment.Status.ACTIVE,
    ).first()
    if assignment is None:
        raise ValidationError('A participação não está ativa para este evento.')
    credential = Credential.objects.select_for_update().filter(
        pk=credential.pk,
        event_assignment=assignment,
        status=Credential.Status.ACTIVE,
    ).first()
    if credential is None:
        raise ValidationError('A credencial deixou de estar ativa. Leia novamente.')

    last_movement = Movement.objects.filter(
        event_assignment=assignment,
        correction__isnull=True,
    ).order_by('-recorded_at', '-pk').first()
    actual_type = next_movement_type(last_movement)
    actual_last_id = last_movement.pk if last_movement else None
    if expected_type != actual_type or expected_last_movement_id != actual_last_id:
        raise ValidationError(
            'A situação mudou desde a leitura. Confira a nova ação sugerida e confirme novamente.'
        )

    try:
        with transaction.atomic():
            movement = Movement.objects.create(
                request_id=request_id,
                event=event,
                event_assignment=assignment,
                credential=credential,
                movement_type=actual_type,
                recorded_by=actor,
            )
    except IntegrityError:
        prior_request = Movement.objects.filter(request_id=request_id).first()
        if (
            prior_request
            and prior_request.event_id == event.pk
            and prior_request.credential_id == credential_id
            and prior_request.recorded_by_id == actor.pk
        ):
            return prior_request, False
        raise ValidationError('A confirmação foi processada em outra solicitação.')
    return movement, True


@transaction.atomic
def invalidate_latest_movement(*, event_id, organization_id, movement_id, actor, reason):
    reason = reason.strip()
    if len(reason) < 10:
        raise ValidationError({'reason': 'A justificativa deve ter pelo menos 10 caracteres.'})
    if len(reason) > 500:
        raise ValidationError({'reason': 'A justificativa não pode ultrapassar 500 caracteres.'})

    event = Event.objects.filter(
        pk=event_id,
        organization_id=organization_id,
        organization__is_active=True,
    ).first()
    if event is None:
        raise ValidationError('O evento não está disponível para correção.')

    membership = OrganizationMembership.objects.select_for_update().filter(
        organization_id=organization_id,
        user=actor,
        user__is_active=True,
        is_active=True,
    ).first()
    if membership is None or membership.role not in MANAGER_ROLES:
        raise PermissionDenied('Somente administradores e supervisores podem corrigir movimentações.')

    movement = Movement.objects.filter(
        pk=movement_id,
        event=event,
        event_assignment__organization_id=organization_id,
        event_assignment__event=event,
    ).first()
    if movement is None:
        raise ValidationError('A movimentação não pertence a este evento.')

    assignment = EventAssignment.objects.select_for_update().filter(
        pk=movement.event_assignment_id,
        event=event,
        organization_id=organization_id,
    ).first()
    if assignment is None:
        raise ValidationError('A participação não pertence a este evento.')
    movement = Movement.objects.select_for_update().filter(
        pk=movement.pk,
        event=event,
        event_assignment=assignment,
    ).first()
    if movement is None:
        raise ValidationError('A movimentação não está disponível para correção.')
    if MovementCorrection.objects.filter(movement=movement).exists():
        raise ValidationError('Esta movimentação já foi invalidada.')

    latest_valid = Movement.objects.filter(
        event_assignment=assignment,
        correction__isnull=True,
    ).order_by('-recorded_at', '-pk').first()
    if latest_valid is None or latest_valid.pk != movement.pk:
        raise ValidationError(
            'Corrija primeiro as movimentações posteriores, da mais recente para a mais antiga.'
        )

    try:
        with transaction.atomic():
            correction = MovementCorrection.objects.create(
                movement=movement,
                reason=reason,
                corrected_by=actor,
            )
    except IntegrityError as error:
        raise ValidationError('Esta movimentação já foi corrigida por outra solicitação.') from error
    return correction
