from django.urls import path

from . import views

app_name = 'events'

urlpatterns = [
    path('organizations/<slug:org_slug>/events/', views.event_list, name='list'),
    path('organizations/<slug:org_slug>/events/new/', views.event_create, name='create'),
    path('organizations/<slug:org_slug>/events/<int:pk>/', views.event_detail, name='detail'),
    path('organizations/<slug:org_slug>/events/<int:pk>/edit/', views.event_edit, name='edit'),
]
