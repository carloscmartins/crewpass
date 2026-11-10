from django.contrib import admin

from .models import Organization, OrganizationMembership


class OrganizationMembershipInline(admin.TabularInline):
    model = OrganizationMembership
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'legal_name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'legal_name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (OrganizationMembershipInline,)


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'organization')
    search_fields = ('user__email', 'organization__name')
