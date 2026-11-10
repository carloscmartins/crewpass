from django.contrib.auth.views import LoginView

from .forms import EmailAuthenticationForm


class EmailLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = 'accounts/login.html'
