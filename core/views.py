from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.urls import resolve, reverse
from .models import User
from .models import Message, Patient, Professional
from .helpers import ask_openai, create_patient
from django.http import JsonResponse
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

def professional_detail(request, slug):
    professional = get_object_or_404(Professional, slug=slug)
    return render(request, 'professionals_details.html', {'professional': professional})

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


