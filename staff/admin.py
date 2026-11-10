from django.contrib import admin

from .models import (
    Company,
    EventAssignment,
    EventAssignmentShift,
    Shift,
    StaffMember,
    StaffRole,
    TeamCategory,
)


class StaffRoleInline(admin.TabularInline):
    model = StaffRole
    extra = 1
    can_delete = False
    fields = ('name', 'is_active')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'trade_name', 'organization', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('legal_name', 'trade_name', 'document')


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'organization', 'email', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('full_name', 'email', 'document')


@admin.register(TeamCategory)
class TeamCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('name',)
    inlines = (StaffRoleInline,)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.organization = form.instance.organization
            instance.team_category = form.instance
            instance.save()
        for deleted in formset.deleted_objects:
            deleted.delete()
        formset.save_m2m()


@admin.register(EventAssignment)
class EventAssignmentAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'event', 'company', 'status')
    list_filter = ('organization', 'event', 'status')
    search_fields = ('staff_member__full_name', 'event__name')

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.credentials.exists():
            readonly_fields.extend(('event', 'staff_member'))
        if obj and obj.access_movements.exists():
            readonly_fields.extend(('company', 'team_category', 'staff_role'))
        return tuple(dict.fromkeys(readonly_fields))


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'starts_at', 'ends_at', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('name',)


@admin.register(EventAssignmentShift)
class EventAssignmentShiftAdmin(admin.ModelAdmin):
    list_display = ('event_assignment', 'shift', 'created_by')
    list_filter = ('event_assignment__organization', 'event_assignment__event')
    search_fields = ('event_assignment__staff_member__full_name', 'event_assignment__event__name')
