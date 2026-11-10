from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import EmailLoginView

app_name = 'accounts'

urlpatterns = [
    path('login/', EmailLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
