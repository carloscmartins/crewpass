from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('organizations/<slug:org_slug>/reports/', views.event_list, name='event_list'),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/reports/',
        views.dashboard,
        name='dashboard',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/reports/present/',
        views.present_list,
        name='present_list',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/reports/movements/',
        views.movement_history,
        name='history',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/reports/movements.csv',
        views.movement_csv,
        name='movement_csv',
    ),
]
