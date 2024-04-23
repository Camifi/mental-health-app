from django.shortcuts import get_object_or_404, render, redirect
from .models import Message, Patient, Professional, Session, User
from .helpers import ask_openai, create_patient
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from .models import Message, Patient 
from .prompts import get_initial_prompt, get_patient_completed_prompt, get_session_recommendation, get_session_custom_request, get_session_csv_report, get_professional_prompt
from django.contrib.auth.decorators import login_required
from .forms import SessionForm
from django.contrib import messages
import csv
import io

def chatbot(request):
    if request.user.user_type != User.UserTypeChoices.PATIENT:
        return HttpResponseForbidden("No autorizado")
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

# myTODO: vista chatbot profesional 
def chatbot_profesional(request):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")
    
    if not request.user.is_completed:
        return redirect('complete_professional_profile')

    if request.method == 'POST':
        message_content = request.POST.get('message')
        
        # Guardar mensaje de usuario
        user_message = Message(user=request.user, content=message_content, is_from_user=True)
        user_message.save()

        chats = Message.objects.filter(user=request.user).order_by('id')

        # Intenta obtener el registro de Patient para el usuario actual
        professional = Professional.objects.get(user=request.user)
        initial_message = get_professional_prompt(professional, request.user)
        
        # Si está completo, enviar un mensaje de bienvenida personalizado.
        response_content = ask_openai(chats, initial_message)
        
        # Guardar la respuesta del bot y enviarla al usuario
        bot_response = Message(user=request.user, content=response_content, is_from_user=False)
        bot_response.save()

        return JsonResponse({'message': message_content, 'response': response_content})
    else:
        # Cuando el usuario entra al chatbot, mostrarle los mensajes previos o la interfaz inicial.
        chats = Message.objects.filter(user=request.user).order_by('id')
        user_id = request.user.id
        return render(request, 'professional/chatbot.html', {'chats': chats, 'user_id': user_id})

def welcome_professional(request):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")
    return render(request,'professional/home.html')

@login_required
def dashboard_patient(request):
    if request.user.user_type != User.UserTypeChoices.PATIENT:
        return HttpResponseForbidden("No autorizado")
    user = request.user
    return render(request,'patient/home.html', {'user': user})

@login_required
def list_patients(request):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")
    if not request.user.is_completed:
        return redirect('complete_professional_profile')
    try:
        professional = Professional.objects.get(user=request.user)
        patients = professional.patients.all()
    except Professional.DoesNotExist:
        # Manejo del caso en que el usuario no tenga un perfil de profesional asociado
        patients = []
    
    return render(request, 'professional/patients_list.html', {'patients': patients})


@login_required
def show_patient(request, id):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")

    professional = get_object_or_404(Professional, user=request.user)
    patient = get_object_or_404(Patient, id=id, professional=professional)
    sessions = Session.objects.filter(patient=patient, professional=professional)

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            new_session = form.save(commit=False)
            new_session.professional = professional
            new_session.patient = patient  # Asegurar que el paciente se establece
            new_session.save()
            return redirect('show_patient', id=id)
    else:
        form = SessionForm()

    custom_prompt = request.GET.get("custom-prompt")
    if custom_prompt:
        prompt = get_session_custom_request(patient, sessions, custom_prompt)
    else:
        prompt = get_session_recommendation(patient, sessions)

    recommendation = ask_openai([], prompt)

    return render(request, 'professional/patient_detail.html', {
        'patient': patient,
        'sessions': sessions,
        'form': form,  # Asegúrate de pasar el formulario al template
        'recommendation': recommendation
    })
#sesiones
@login_required
def create_session(request, patient_id):
    professional = Professional.objects.get(user=request.user)
    patient = get_object_or_404(Patient, id=patient_id)  # Asegúrate de que el paciente existe

    if request.method == 'POST':
        form = SessionForm(request.POST, professional=professional)
        if form.is_valid():
            session = form.save(commit=False)
            session.professional = professional
            session.patient = patient
            session.save()
            messages.success(request, 'La sesión ha sido creada exitosamente.')
            return redirect('core:professional_patient_detail', id=patient_id)
    else:
        form = SessionForm(professional=professional)

    context = {
        'form': form,
        'patient_id': patient_id,  # Asegúrate de pasar esto
        'session': None
    }
    return render(request, 'professional/session_form.html', context)

@login_required
def edit_session(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL or session.patient.professional.user != request.user:
        return HttpResponseForbidden("No autorizado")

    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sesión actualizada correctamente.')
            return redirect('core:professional_patient_detail', id=session.patient.id)
    else:
        form = SessionForm(instance=session)

    context = {
        'form': form,
        'patient_id': session.patient.id,  # Asegúrate de pasar esto
        'session': session
    }
    return render(request, 'professional/session_form.html', context)


@login_required
def delete_session(request, pk):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")
    session = get_object_or_404(Session, pk=pk)
    # Asegurar que el paciente asociado a la sesión esté bajo el cuidado del profesional actual
    if session.patient.professional.user != request.user:
        return redirect('core:session_list')  # O puedes mostrar un mensaje de error
    
    if request.method == 'POST':
        session.delete()
        return redirect('core:professional_patient_detail', id=session.patient.id)
    return render(request, 'professional/session_confirm_delete.html', {'session': session})



@login_required

def connectProfessional(request, professional_id):
    if request.user.user_type != User.UserTypeChoices.PATIENT:
        return HttpResponseForbidden("No autorizado")
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

    messages.success(request, 'Conexión con el profesional realizada con éxito.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def disconnectProfessional(request):
    user = request.user
    patient = Patient.objects.get(user=user.id)
    patient.professional = None
    patient.save()

    messages.success(request, 'Desconexión del profesional realizada con éxito.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))



@login_required
def session_list(request):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")

    if not request.user.is_completed:
        return redirect('complete_professional_profile')

    professional = Professional.objects.get(user=request.user)
    queryset = Session.objects.filter(professional=professional)

    # Filtros
@login_required
def session_list(request):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")
    professional = request.user.professional_profile
    queryset = Session.objects.filter(professional=professional).select_related('patient')

    # Filtros
    patient_id = request.GET.get('patient')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if patient_id:
        queryset = queryset.filter(patient__id=patient_id)
    if date_from:
        queryset = queryset.filter(session_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(session_date__lte=date_to)

    return render(request, 'professional/session_list.html', {
        'sessions': queryset,
        'patients': professional.patients.all(),  # Suponiendo que la relación es patients en Professional
    })


@login_required
def generate_report(request, id):
    professional = get_object_or_404(Professional, user=request.user)
    patient = get_object_or_404(Patient, id=id, professional=professional)
    sessions = Session.objects.filter(patient=patient, professional=professional)

    prompt = get_session_csv_report(patient, sessions)

    # Obtener la respuesta de GPT
    report_text = ask_openai([], prompt)

    # Crear un archivo CSV en memoria
    report_csv = io.StringIO()
    csv_writer = csv.writer(report_csv)

    # Convertir la respuesta de texto plano en filas de CSV
    csv_reader = csv.reader(report_text.splitlines())
    for row in csv_reader:
        csv_writer.writerow(row)

    # Configurar la respuesta HTTP con el contenido del archivo CSV en memoria
    response = HttpResponse(report_csv.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f"attachment; filename=\"reporte-{patient.user.username}.csv\""

    return response
