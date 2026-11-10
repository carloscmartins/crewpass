from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('organizations.urls')),
    path('', include('events.urls')),
    path('', include('staff.urls')),
    path('', include('credentials.urls')),
    path('', include('access_control.urls')),
    path('', include('reports.urls')),
]
