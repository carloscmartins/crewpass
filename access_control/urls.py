from django.urls import path

from . import views

app_name = 'access_control'

urlpatterns = [
    path(
        'organizations/<slug:org_slug>/operations/',
        views.event_list,
        name='event_list',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/access/',
        views.operation,
        name='operation',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/operators/',
        views.operator_management,
        name='operator_management',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/movements/'
        '<int:movement_id>/correct/',
        views.movement_correction,
        name='movement_correction',
    ),
]
