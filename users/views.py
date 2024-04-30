from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic.edit import DeleteView
from core.models import Patient, Professional
from users.models import Post, User
from users.forms import CustomUserCreationForm
from django.contrib import messages
from .forms import CustomUserCreationForm, ProfessionalAdditionalInfoForm, UserCommonInfoForm, PatientProfileForm
from django.http import HttpResponseForbidden

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
            user = form.save()
            login(request, user)
            return redirect('select_user_type')
        else:
            pass
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})


#selecciona el tipo de usuario y almacena en su tabla correspondiente
@login_required(login_url="signin")
def complete_user_common_info(request):
    if request.method == "POST":
        form = UserCommonInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                messages.success(request, 'Tu información ha sido actualizada exitosamente.')
                return redirect('complete_user_common_info')
    else:
        form = UserCommonInfoForm(instance=request.user)

    if request.user.user_type == "PR":  # Asume que "PR" indica un usuario profesional
        base_template = 'professional/base.html'
    else:
        base_template = 'patient/base.html'

    context = {
        'form': form,
        'base_template': base_template  # Pasar el nombre del template base al contexto
    }
    return render(request, 'complete_user_info.html', context)


@login_required(login_url="signin")
def complete_professional_profile(request):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")
    # Obtenemos el perfil del profesional, creándolo si no existe
    profile, created = Professional.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Pasamos request.POST y request.FILES al formulario, junto con la instancia del perfil
        form = ProfessionalAdditionalInfoForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            request.user.save()
            messages.success(request, 'Perfil actualizado exitosamente.')  
            return redirect('complete_professional_profile')  
        else:
            # Agrega un mensaje de error si el formulario no es válido
            messages.error(request, 'Error al actualizar el perfil. Por favor, revise los datos ingresados.')
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
    

    
def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def my_custom_page_not_found_view(request, exception):
    return render(request, '404.html', {}, status=404)


#blog
def blog_index(request):
    posts = Post.objects.all().order_by('-created_on')
    context = {
        'posts': posts
    }
    return render(request, 'blog_index.html', context)

def blog_detail(request, pk):
    post = Post.objects.get(pk=pk)
    context = {
        'post': post
    }
    return render(request, 'blog_detail.html', context)


def edit_patient_profile(request):
    # Asume que el usuario ha iniciado sesión
    user = request.user
    if not user.is_completed:
        # Si el perfil no está completo, podrías redirigir o mostrar un mensaje
        return redirect('core:chatbot')  # Redirecciona a la página para completar el perfil

    patient = user.patient_profile
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu información ha sido actualizada exitosamente.')
            return redirect('patient_profile')  # Redirige a la vista del perfil
    else:
        form = PatientProfileForm(instance=patient)

    return render(request, 'patient_profile.html', {'form': form})