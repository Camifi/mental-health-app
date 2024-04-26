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

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un usuario con ese correo electrónico ya existe.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

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
            'birthday': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
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