from django.shortcuts import get_object_or_404, render, redirect
from .models import Message, Patient, Professional
from .helpers import ask_openai, create_patient
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from .models import Message, Patient  
from .prompts import get_initial_prompt, get_patient_completed_prompt
from django.contrib.auth.decorators import login_required

def chatbot(request):
    if request.method == 'POST':
        message_content = request.POST.get('message')
        
        # Guardar mensaje de usuario
        user_message = Message(user=request.user, content=message_content, is_from_user=True)
        user_message.save()

        chats = Message.objects.filter(user=request.user).order_by('id')

        # Verificar si el perfil del usuario está completo.
        if request.user.is_completed:
            # Intenta obtener el registro de Patient para el usuario actual
            patient = Patient.objects.get(user=request.user)
            initial_message = get_patient_completed_prompt(patient, request.user)
            
            # Si está completo, enviar un mensaje de bienvenida personalizado.
            response_content = ask_openai(chats, initial_message)
        else:
            # Si no está completo, invocar a OpenAI y crear perfil.
            
            initial_message = get_initial_prompt(1)
            response_content = ask_openai(chats, initial_message)
            print("Primera respuesta")
            print(response_content)
            
            # Si la respuesta incluye 'CONFIRMED', procesar la información.
            if "CONFIRMED" in response_content:
                print("CONFIRMED encontrado")
                initial_message = get_initial_prompt(2)
                json_content = ask_openai(chats, initial_message)
                result = create_patient(json_content, request.user)

                if result:
                    # Actualizar el perfil del usuario para reflejar que está completo.
                    request.user.is_completed = True
                    request.user.save()
                    Message.objects.filter(user=request.user).delete()
                    final_message = get_initial_prompt(3)
                    response_content = ask_openai(chats, final_message)
                    print("Segunda respuesta")
                    print(response_content)
            
        
        # Guardar la respuesta del bot y enviarla al usuario
        bot_response = Message(user=request.user, content=response_content, is_from_user=False)
        bot_response.save()

        return JsonResponse({'message': message_content, 'response': response_content})
    
    else:
        # Cuando el usuario entra al chatbot, mostrarle los mensajes previos o la interfaz inicial.
        chats = Message.objects.filter(user=request.user).order_by('id')
        user_id = request.user.id
        return render(request, 'patient/chatbot.html', {'chats': chats, 'user_id': user_id})


#Mostrar lista de profesionales 
def list_professionals(request):
    professionals = Professional.objects.all()  # Obtén todos los objetos Professional
    return render(request, 'list_professionals.html', {'professionals': professionals})

@login_required
def professional_detail(request, slug):
    professional = get_object_or_404(Professional, slug=slug)
    user = request.user
    patient = Patient.objects.get(user=user.id)
    return render(request, 'professionals_details.html', {'professional': professional, 'patient': patient})

def clear_chat(request, user_id):
    # Obtener todos los mensajes del usuario especificado
    messages_to_delete = Message.objects.filter(user_id=user_id)
    
    # Eliminar los mensajes
    messages_to_delete.delete()
    
    # Redirigir a otra vista
    return redirect('core:chatbot')

#vista chatbot profesional 
def chatbot_profesional(request):
        return render(request,'professional\chatbot.html')

def welcome_professional(request):
        return render(request,'professional\home.html')

@login_required
def dashboard_patient(request):
    user = request.user
    return render(request,'patient\home.html', {'user': user})

@login_required
def list_patients(request):
    try:
        professional = Professional.objects.get(user=request.user)
        patients = professional.patients.all()
    except Professional.DoesNotExist:
        # Manejo del caso en que el usuario no tenga un perfil de profesional asociado
        patients = []
    
    return render(request, 'professional\patients_list.html', {'patients': patients})

@login_required
def show_patient(request, id):
    try:
        professional = Professional.objects.get(user=request.user)
    except Professional.DoesNotExist:
        # Si el usuario no tiene un perfil de profesional, devuelve un 404 directamente.
        raise Http404("No se encontró el perfil profesional correspondiente.")

    # Intenta obtener el paciente asegurándote de que pertenezca al profesional actual.
    # Usamos 'get_object_or_404' para levantar automáticamente un 404 si el paciente no existe o no pertenece al profesional.
    patient = get_object_or_404(Patient, id=id, professional=professional)

    return render(request, 'professional/patient_detail.html', {'patient': patient})

@login_required
def connectProfessional(request, professional_id):
    # Recupera el usuario de la sesión
    user = request.user
    
    # Intenta recuperar el perfil de Patient asociado al usuario
    try:
        patient = Patient.objects.get(user=user)
    except Patient.DoesNotExist:
        # Si el usuario no tiene un perfil de Patient, redirige a la página anterior
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    # Verifica si el Patient ya tiene un Professional asignado
    if patient.professional is not None:
        # Si ya tiene un Professional asignado, redirige a la página anterior
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    # Verifica que el Professional con el ID proporcionado exista
    professional = get_object_or_404(Professional, pk=professional_id)

    # Asigna el Professional al Patient y guarda el cambio
    patient.professional = professional
    patient.save()

    # Redirige al usuario a la página anterior
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def disconnectProfessional(request):
    user = request.user
    patient = Patient.objects.get(user=user.id)
    patient.professional = None
    patient.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))