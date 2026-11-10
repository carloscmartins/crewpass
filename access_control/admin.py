from django.contrib import admin

from .models import EventOperatorGrant, Movement, MovementCorrection


@admin.register(EventOperatorGrant)
class EventOperatorGrantAdmin(admin.ModelAdmin):
    list_display = ('event', 'membership', 'is_active', 'granted_by', 'granted_at', 'revoked_at')
    list_filter = ('is_active', 'event__organization')
    search_fields = ('event__name', 'membership__user__email')
    readonly_fields = (
        'event',
        'membership',
        'is_active',
        'granted_by',
        'granted_at',
        'revoked_by',
        'revoked_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ('event', 'event_assignment', 'movement_type', 'recorded_by', 'recorded_at')
    list_filter = ('movement_type', 'event')
    search_fields = (
        'event__name',
        'event_assignment__staff_member__full_name',
        'recorded_by__email',
    )
    readonly_fields = (
        'request_id',
        'event',
        'event_assignment',
        'credential',
        'movement_type',
        'occurred_at',
        'recorded_at',
        'recorded_by',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MovementCorrection)
class MovementCorrectionAdmin(admin.ModelAdmin):
    list_display = ('movement', 'corrected_by', 'corrected_at')
    list_filter = ('corrected_at', 'movement__event')
    search_fields = ('movement__event_assignment__staff_member__full_name', 'corrected_by__email')
    readonly_fields = ('movement', 'reason', 'corrected_by', 'corrected_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
