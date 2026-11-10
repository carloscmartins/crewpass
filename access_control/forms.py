from django import forms

from organizations.models import OrganizationMembership


class ManualSearchForm(forms.Form):
    query = forms.CharField(
        label='Nome ou CPF completo',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'inputmode': 'search',
                'placeholder': 'Digite um nome ou os 11 dígitos do CPF',
            }
        ),
    )


class ScanLookupForm(forms.Form):
    credential_code = forms.CharField(max_length=64, widget=forms.HiddenInput)


class MovementConfirmationForm(forms.Form):
    credential_id = forms.IntegerField(widget=forms.HiddenInput)
    expected_type = forms.ChoiceField(
        choices=(('ENTRY', 'Entrada'), ('EXIT', 'Saída')),
        widget=forms.HiddenInput,
    )
    last_movement_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    request_id = forms.UUIDField(widget=forms.HiddenInput)
    confirm = forms.BooleanField(
        label='Confirmo o registro da movimentação sugerida.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )


class GrantOperatorForm(forms.Form):
    membership = forms.ModelChoiceField(
        queryset=OrganizationMembership.objects.none(),
        label='Operador da organização',
        empty_label='Selecione um operador',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    confirm = forms.BooleanField(
        label='Confirmo que este operador poderá registrar movimentações neste evento.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership'].queryset = OrganizationMembership.objects.filter(
            organization=organization,
            is_active=True,
            role=OrganizationMembership.Role.OPERATOR,
            user__is_active=True,
        ).select_related('user')


class RevokeOperatorForm(forms.Form):
    grant_id = forms.IntegerField(widget=forms.HiddenInput)
    confirm = forms.BooleanField(
        label='Confirmo a revogação deste acesso ao evento.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )


class MovementCorrectionForm(forms.Form):
    movement_id = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(
        label='Justificativa da correção',
        min_length=10,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 4,
                'maxlength': 500,
                'placeholder': 'Explique por que este último registro válido deve ser invalidado.',
            }
        ),
    )
    confirm = forms.BooleanField(
        label='Confirmo a invalidação desta movimentação. O registro original será preservado.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )
