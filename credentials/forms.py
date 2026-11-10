from django import forms


class ConfirmCredentialActionForm(forms.Form):
    confirm = forms.BooleanField(
        label='Confirmo esta ação para a credencial selecionada.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )
