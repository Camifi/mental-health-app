from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from core.models import CityOption, Patient, Professional

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    # Añade tus campos personalizados aquí
    full_name = forms.CharField(required=True)
    phone_number = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        # Asegúrate de incluir los campos adicionales que quieres mostrar en el formulario
        fields = UserCreationForm.Meta.fields + ('full_name', 'phone_number', 'email')

    def save(self, commit=True):
        # Guarda los datos proporcionados por el formulario con el usuario
        user = super().save(commit=False)
        user.full_name = self.cleaned_data['full_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserCommonInfoForm(forms.ModelForm):
    city = forms.ModelMultipleChoiceField(
        queryset=CityOption.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['gender', 'birthday', 'city']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            # Asumiendo que quieres mantener el widget por defecto para 'gender' y 'birthday'
        }

# Formulario para actualizar la información adicional del profesional
class ProfessionalAdditionalInfoForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = [
            'title',
            'specialization',
            'certifications_or_courses',
            'therapeutic_approaches',
            'demographic_groups_served',
            'session_modalities',
            'availability',
            'city_served',
            'biography', 
            'profile_image',
        ]
        widgets = {
            'biography': forms.Textarea(attrs={'rows': 4, 'cols': 40}),  # Usa Textarea para la biografía
        }