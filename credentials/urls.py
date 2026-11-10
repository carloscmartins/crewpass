from django.urls import path

from . import views

app_name = 'credentials'

urlpatterns = [
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/credentials/',
        views.credential_list,
        name='list',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/'
        'assignments/<int:assignment_id>/credentials/issue/',
        views.credential_issue,
        name='issue',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/'
        'credentials/<int:credential_id>/print/',
        views.credential_print,
        name='print',
    ),
    path(
        'organizations/<slug:org_slug>/events/<int:event_id>/'
        'credentials/<int:credential_id>/<str:action>/',
        views.credential_action,
        name='action',
    ),
]
