from django import forms
from .models import Patient, Session

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['session_date', 'objectives', 'difficulties']
        widgets = {
            'session_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'objectives': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'difficulties': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        professional = kwargs.pop('professional', None)
        super(SessionForm, self).__init__(*args, **kwargs)

class PatientSessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['session_date', 'objectives', 'difficulties', 'patient']  
        widgets = {
            'session_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'objectives': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'difficulties': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        professional = kwargs.pop('professional', None)
        super(PatientSessionForm, self).__init__(*args, **kwargs)
        if professional and 'patient' in self.fields:  # Verificación adicional para evitar KeyError
            self.fields['patient'].queryset = Patient.objects.filter(professional=professional)