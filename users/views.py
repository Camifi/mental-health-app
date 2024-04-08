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
    return render(request,'home.html')

@login_required
def select_user_type(request):
    # Verificar si el usuario ya tiene un tipo de usuario establecido
    if getattr(request.user, 'user_type', None):
        message = "Ya has seleccionado tu tipo de usuario."
        messages.add_message(request, messages.INFO, message)
        return redirect('home')  # O la página de inicio adecuada según el tipo de usuario

    if request.method == "POST":
        user_type = request.POST.get('user_type')
        request.user.user_type = user_type
        request.user.save()

        # Redirige a todos los usuarios para completar su información común primero
        return redirect('complete_user_common_info')

    return render(request, 'registration/select_user_type.html')
     

def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Verifica el tipo de usuario para redirigirlo correctamente
            user_type = getattr(user, 'user_type', None)  # Obtiene user_type o None si no existe
            if user_type == 'P':  # Si el usuario es un paciente
                return redirect('core:patient_home')  # Redirige a la página de bienvenida para pacientes
            elif user_type == 'PR':  # Si el usuario es un profesional
                return redirect('core:professional_home')  # Redirige al dashboard de profesionales
            else:
                # Si user_type no está definido, redirige a una página de selección de tipo de usuario o manejo de error
                return redirect('select_user_type')
        else:
            # En caso de formulario no válido
            messages.error(request, 'Usuario y/o contraseña incorrectos.')
            return redirect('signin')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/signin.html', {"form": form})


@login_required(login_url="signin")
def professional_dashboard(request):
    # Aquí iría cualquier lógica para recoger los datos que necesitas pasar a la plantilla.
    return render(request, 'dashboard_professional.html')
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # El formulario se encarga de crear el usuario
            login(request, user)
            return redirect('select_user_type')
        else:
            # Si el formulario no es válido, volvemos a mostrar el formulario con errores
            return render(request, 'registration/signup.html', {"form": form})
    else:
        form = CustomUserCreationForm()
        return render(request, 'registration/signup.html', {"form": form})

    
#selecciona el tipo de usuario y almacena en su tabla correspondiente
@login_required(login_url="signin")
def complete_user_common_info(request):
    if request.method == "POST":
        # Aquí asumes que tienes un formulario para la información común
        form = UserCommonInfoForm(request.POST)
        if form.is_valid():
            user_common_info = form.save(commit=False)
            user_common_info.user = request.user
            user_common_info.save()

            # Comprobar el tipo de usuario y redirigir adecuadamente
            if request.user.user_type == "PR":  # Profesional
                return redirect('complete_professional_profile')
            else:  # Paciente
                return redirect('core:welcome')
    else:
        form = UserCommonInfoForm()
    
    return render(request, 'complete_user_info.html', {'form': form})


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