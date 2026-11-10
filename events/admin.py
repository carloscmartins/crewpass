from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'location', 'starts_at', 'ends_at', 'status')
    list_filter = ('status', 'organization')
    search_fields = ('name', 'location')
    date_hierarchy = 'starts_at'
