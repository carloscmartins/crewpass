import re

from django import forms
from django.db.models import Q
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from events.models import Event

from .models import (
    Company,
    EventAssignment,
    EventAssignmentShift,
    Shift,
    StaffMember,
    StaffRole,
    TeamCategory,
)


CONTROL = 'form-control'


class OrganizationModelForm(forms.ModelForm):
    def __init__(self, *args, organization, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', CONTROL)

class CompanyForm(OrganizationModelForm):
    class Meta:
        model = Company
        fields = (
            'legal_name', 'trade_name', 'document', 'contact_name', 'phone', 'email', 'is_active'
        )
        widgets = {
            'legal_name': forms.TextInput(attrs={'autocomplete': 'organization'}),
            'trade_name': forms.TextInput(attrs={'autocomplete': 'organization'}),
            'document': forms.TextInput(
                attrs={'inputmode': 'numeric', 'placeholder': '00.000.000/0000-00'}
            ),
            'phone': forms.TelInput(attrs={'autocomplete': 'tel'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class StaffMemberForm(OrganizationModelForm):
    class Meta:
        model = StaffMember
        fields = ('full_name', 'document', 'phone', 'email', 'company', 'team_category', 'staff_role', 'notes', 'is_active')
        widgets = {
            'full_name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'document': forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'off'}),
            'phone': forms.TelInput(attrs={'autocomplete': 'tel'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, organization=organization, **kwargs)
        self.fields['company'].queryset = Company.objects.filter(
            organization=organization,
            is_active=True,
        )
        self.fields['company'].required = False
        self.fields['company'].empty_label = 'Sem empresa vinculada'
        self.fields['team_category'].queryset = TeamCategory.objects.filter(
            organization=organization,
            is_active=True,
        )
        self.fields['team_category'].required = False
        self.fields['team_category'].empty_label = 'Sem categoria'
        self.fields['staff_role'].queryset = StaffRole.objects.filter(
            organization=organization,
            team_category__isnull=False,
            is_active=True,
        ).select_related('team_category').order_by('team_category__name', 'name')
        self.fields['staff_role'].required = False
        self.fields['staff_role'].empty_label = 'Sem função'
        self.fields['staff_role'].widget = CategoryRoleSelect(
            role_categories={
                str(role.pk): role.team_category_id
                for role in self.fields['staff_role'].queryset
            },
            attrs={'class': CONTROL},
        )
        self.fields['staff_role'].widget.choices = [
            ('', 'Sem função'),
            *[
                (role.pk, f'{role.team_category.name} — {role.name}')
                for role in self.fields['staff_role'].queryset
            ],
        ]

    def clean_document(self):
        value = re.sub(r'\D', '', self.cleaned_data.get('document', ''))
        if not value:
            return ''
        matches = StaffMember.objects.filter(
            organization=self.organization,
            document=value,
        )
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise forms.ValidationError(
                'Já existe um profissional com este CPF nesta organização.'
            )
        return value


class CatalogForm(OrganizationModelForm):
    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        matches = self._meta.model.objects.filter(organization=self.organization, name__iexact=name)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise forms.ValidationError('Já existe um cadastro com este nome nesta organização.')
        return name


class TeamCategoryForm(CatalogForm):
    unlinked_roles = forms.ModelMultipleChoiceField(
        queryset=StaffRole.objects.none(),
        label='Vincular funções existentes sem categoria',
        help_text='Use somente para organizar cadastros antigos que ainda não têm categoria.',
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 5}),
    )

    class Meta:
        model = TeamCategory
        fields = ('name', 'is_active')
        widgets = {'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'})}
        labels = {'name': 'Nome da categoria'}

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, organization=organization, **kwargs)
        unlinked_roles = StaffRole.objects.filter(
            organization=organization,
            team_category__isnull=True,
            is_active=True,
        )
        if unlinked_roles.exists():
            self.fields['unlinked_roles'].queryset = unlinked_roles.order_by('name')
        else:
            self.fields.pop('unlinked_roles')


class StaffRoleInlineForm(forms.ModelForm):
    class Meta:
        model = StaffRole
        fields = ('name', 'is_active')
        widgets = {'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'})}

    def __init__(self, *args, organization, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', CONTROL)

    def has_changed(self):
        if (
            not self.instance.pk
            and not self.data.get(self.add_prefix('name'))
            and not self.data.get(self.add_prefix('is_active'))
        ):
            return False
        return super().has_changed()

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        category_id = self.instance.team_category_id
        if category_id:
            matches = StaffRole.objects.filter(
                organization=self.organization,
                team_category_id=category_id,
                name__iexact=name,
            )
            if self.instance.pk:
                matches = matches.exclude(pk=self.instance.pk)
            if matches.exists():
                raise forms.ValidationError(
                    'Já existe essa função nesta categoria.'
                )
        return name


class StaffRoleInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, organization, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        return {**super().get_form_kwargs(index), 'organization': self.organization}

    def clean(self):
        super().clean()
        names = set()
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or form.errors:
                continue
            name = form.cleaned_data.get('name', '').strip().casefold()
            if not name:
                continue
            if name in names:
                form.add_error('name', 'Informe cada função uma única vez nesta categoria.')
            names.add(name)

    def save_new(self, form, commit=True):
        instance = form.save(commit=False)
        instance.organization = self.organization
        instance.team_category = self.instance
        if commit:
            instance.save()
        return instance

    def save_existing(self, form, instance, commit=True):
        instance = form.save(commit=False)
        instance.organization = self.organization
        instance.team_category = self.instance
        if commit:
            instance.save()
        return instance


StaffRoleFormSet = inlineformset_factory(
    TeamCategory,
    StaffRole,
    form=StaffRoleInlineForm,
    formset=StaffRoleInlineFormSet,
    fields=('name', 'is_active'),
    extra=1,
    can_delete=False,
)


class CategoryRoleSelect(forms.Select):
    def __init__(self, *args, role_categories=None, **kwargs):
        self.role_categories = role_categories or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        category_id = self.role_categories.get(str(value))
        if category_id:
            option['attrs']['data-category-id'] = str(category_id)
        return option


class EventAssignmentForm(OrganizationModelForm):
    shift = forms.ModelChoiceField(
        label='Turno previsto',
        queryset=Shift.objects.none(),
        required=False,
        empty_label='Sem turno previsto',
        widget=forms.Select(attrs={'class': CONTROL}),
    )

    class Meta:
        model = EventAssignment
        fields = (
            'event', 'staff_member', 'status', 'notes'
        )
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'status': forms.Select(),
        }

    def __init__(self, *args, organization, include_event_staff=True, **kwargs):
        super().__init__(*args, organization=organization, **kwargs)
        self.instance.organization = organization
        self.fields['shift'].queryset = Shift.objects.filter(
            organization=organization,
            is_active=True,
        ).order_by('name')

        event_queryset = Event.objects.filter(organization=organization).exclude(
            status=Event.Status.CANCELLED
        )
        if self.instance.event_id:
            event_queryset = event_queryset | Event.objects.filter(
                organization=organization,
                pk=self.instance.event_id,
            )
        self.fields['event'].queryset = event_queryset

        self.fields['staff_member'].queryset = StaffMember.objects.filter(
            organization=organization,
            is_active=True,
        )
        if self.instance.staff_member_id:
            self.fields['staff_member'].queryset = StaffMember.objects.filter(
                organization=organization,
            ).filter(Q(is_active=True) | Q(pk=self.instance.staff_member_id))

        if self.instance.pk:
            has_credentials = self.instance.credentials.exists()
            has_movements = self.instance.access_movements.exists()
            if has_credentials:
                for field_name in ('event', 'staff_member'):
                    self.fields[field_name].disabled = True
                    self.fields[field_name].help_text = (
                        'Não pode ser alterado após a emissão de uma credencial; '
                        'o histórico permanece vinculado a esta participação.'
                    )
            if has_movements:
                pass
        if not include_event_staff:
            for field_name in ('event', 'staff_member', 'status'):
                self.fields.pop(field_name)


class EventAssociationForm(forms.Form):
    event = forms.ModelChoiceField(
        label='Evento',
        queryset=Event.objects.none(),
        required=False,
        empty_label='Cadastrar somente o perfil do profissional',
        widget=forms.Select(attrs={'class': CONTROL}),
    )

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(
            organization=organization,
        ).exclude(
            status=Event.Status.CANCELLED,
        ).order_by('starts_at', 'name')


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ('name', 'starts_at', 'ends_at', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
            'starts_at': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'ends_at': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, organization, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', CONTROL)

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get('starts_at')
        ends_at = cleaned_data.get('ends_at')
        if starts_at and ends_at and starts_at == ends_at:
            raise forms.ValidationError('O início e o término do turno devem ser diferentes.')
        return cleaned_data


class EventAssignmentShiftForm(forms.ModelForm):
    class Meta:
        model = EventAssignmentShift
        fields = ('shift',)
        widgets = {
            'shift': forms.Select(attrs={'class': CONTROL}),
        }

    def __init__(self, *args, event_assignment, **kwargs):
        self.event_assignment = event_assignment
        super().__init__(*args, **kwargs)
        self.fields['shift'].queryset = Shift.objects.filter(
            organization=event_assignment.organization,
            is_active=True,
        ).order_by('name')
        self.fields['shift'].empty_label = 'Selecione um turno'
        self.fields['shift'].required = True
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', CONTROL)
