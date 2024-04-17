from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic.edit import DeleteView
from core.models import Patient, Professional
from users.models import User
from users.forms import CustomUserCreationForm
from django.contrib import messages
from .forms import CustomUserCreationForm, ProfessionalAdditionalInfoForm, UserCommonInfoForm

def signout(request):
    logout(request)
    return redirect('home')

def homepage(request):
    if request.user.is_authenticated:
        # Supongamos que tienes un campo `user_type` en tu modelo User
        user_type = getattr(request.user, 'user_type', None)
        if user_type == 'P':
            return redirect('core:patient_home')  # Redirige al dashboard del paciente
        elif user_type == 'PR':
            return redirect('core:professional_home')  # Redirige al dashboard del profesional
        # Añade más condiciones según sea necesario

    return render(request,'home.html')

@login_required
def select_user_type(request):
    if getattr(request.user, 'user_type', None):
        return redirect('home')  # Aquí deberías tener una lógica para redirigir según el tipo de usuario

    if request.method == "POST":
        user_type = request.POST.get('user_type')
        request.user.user_type = user_type
        request.user.save()

        if user_type == 'P':
            return redirect('complete_user_common_info')  # Asegúrate de que esta vista gestione el redireccionamiento a `core:patient_home`
        elif user_type == 'PR':
            request.session['complete_professional_profile'] = True
            return redirect('complete_user_common_info')  # Asegúrate de que esta vista gestione el redireccionamiento a `core:professional_home`

    return render(request, 'registration/select_user_type.html')

def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            user_type = getattr(user, 'user_type', None)

            if user_type == 'P':
                return redirect('core:patient_home')
            elif user_type == 'PR':
                return redirect('core:professional_home')
            else:
                return redirect('select_user_type')
        else:
            messages.error(request, 'Usuario y/o contraseña incorrectos.')
            return redirect('signin')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/signin.html', {'form': form})



@login_required(login_url="signin")
def professional_dashboard(request):
    # Aquí iría cualquier lógica para recoger los datos que necesitas pasar a la plantilla.
    return render(request, 'dashboard_professional.html')
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Un usuario con ese correo electrónico ya existe.')
                return render(request, 'registration/signup.html', {'form': form})
            user = form.save()
            login(request, user)
            return redirect('select_user_type')
        else:
            return render(request, 'registration/signup.html', {'form': form})
    else:
        form = CustomUserCreationForm()
        return render(request, 'registration/signup.html', {'form': form})
    
#selecciona el tipo de usuario y almacena en su tabla correspondiente
@login_required(login_url="signin")
def complete_user_common_info(request):
    is_editing = request.user.is_completed if hasattr(request.user, 'is_completed') else False
    
    if request.method == "POST":
        form = UserCommonInfoForm(request.POST, instance=request.user)  # Pasamos la instancia del usuario actual
        if form.is_valid():
            form.save()
            if not is_editing:
                request.user.is_completed = True  # Marcar como completado si es la primera vez
                request.user.save()
            messages.success(request, 'Tu información ha sido actualizada exitosamente.')

            # Redirigir según el tipo de usuario
            if request.user.user_type == "PR":
                return redirect('core:professional_home')
            else:
                return redirect('core:patient_home')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = UserCommonInfoForm(instance=request.user)  # Inicializa el formulario con los datos del usuario

    context = {
        'form': form,
        'is_editing': is_editing
    }
    return render(request, 'complete_user_info.html', context)


@login_required(login_url="signin")
def complete_professional_profile(request):
    # Obtenemos el perfil del profesional, creándolo si no existe
    profile, created = Professional.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Pasamos request.POST y request.FILES al formulario, junto con la instancia del perfil
        form = ProfessionalAdditionalInfoForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Redirigir a la página de bienvenida específica para profesionales tras guardar
            return redirect('core:professional_home')  # Asegúrate de que el nombre 'profesional-welcome' corresponda a tu URL configurada
    else:
        form = ProfessionalAdditionalInfoForm(instance=profile)

    # Pasamos el formulario a la plantilla
    return render(request, 'complete_professional_profile.html', {'form': form})



class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('home')  # La URL a la que se redirige después de eliminar la cuenta

    def get_object(self, queryset=None):
        """ Sobrescribe este método para obtener el objeto User actual. """
        return self.request.user

    def delete(self, request, *args, **kwargs):
        """
        Llama al método delete() en el objeto obtenido y luego redirige
        a la URL de éxito. Después de eliminar la cuenta, cierra la sesión.
        """
        user = self.get_object()
        response = super().delete(request, *args, **kwargs)  # Elimina el objeto User
        logout(request)  # Cierra la sesión del usuario
        return response