from django import forms

from staff.models import Company, StaffRole, TeamCategory


class PresentFilterForm(forms.Form):
    q = forms.CharField(
        label='Profissional',
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off',
            'placeholder': 'Buscar por nome',
        }),
    )
    company = forms.ModelChoiceField(
        label='Empresa',
        queryset=Company.objects.none(),
        required=False,
        empty_label='Todas',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    category = forms.ModelChoiceField(
        label='Categoria',
        queryset=TeamCategory.objects.none(),
        required=False,
        empty_label='Todas',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    role = forms.ModelChoiceField(
        label='Função',
        queryset=StaffRole.objects.none(),
        required=False,
        empty_label='Todas',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = Company.objects.filter(organization=organization)
        self.fields['category'].queryset = TeamCategory.objects.filter(organization=organization)
        self.fields['role'].queryset = StaffRole.objects.filter(
            organization=organization,
            team_category__isnull=False,
        ).select_related('team_category').order_by('team_category__name', 'name')


class MovementHistoryFilterForm(PresentFilterForm):
    date_from = forms.DateField(
        label='De',
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to = forms.DateField(
        label='Até',
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    movement_type = forms.ChoiceField(
        label='Movimentação',
        required=False,
        choices=(('', 'Todas'), ('ENTRY', 'Entrada'), ('EXIT', 'Saída')),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    validity = forms.ChoiceField(
        label='Situação do registro',
        required=False,
        choices=(('', 'Todas'), ('valid', 'Válidas'), ('corrected', 'Invalidadas')),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', 'A data final deve ser igual ou posterior à inicial.')
        return cleaned_data
