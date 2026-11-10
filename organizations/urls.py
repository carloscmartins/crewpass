from django.urls import path

from . import views

app_name = 'organizations'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('organizations/<slug:slug>/', views.organization_detail, name='detail'),
]
