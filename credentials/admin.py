from django.contrib import admin

from .models import Credential, CredentialAuditLog


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_assignment', 'status', 'issued_at', 'cancelled_at')
    list_filter = ('status', 'event_assignment__event')
    search_fields = ('event_assignment__staff_member__full_name',)
    readonly_fields = (
        'event_assignment',
        'code',
        'status',
        'issued_at',
        'cancelled_at',
        'replaced_by',
        'created_at',
        'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CredentialAuditLog)
class CredentialAuditLogAdmin(admin.ModelAdmin):
    list_display = ('credential', 'action', 'actor', 'replacement', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('credential__event_assignment__staff_member__full_name', 'actor__email')
    readonly_fields = ('credential', 'action', 'actor', 'replacement', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
