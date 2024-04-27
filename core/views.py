from django.shortcuts import get_object_or_404, render, redirect
from .models import Message, Patient, Professional, Session, User, PatientProfessionalConnection, ConnectionStatus
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
    patient = get_object_or_404(Patient, user=user)

    # Intentar obtener cualquier conexión actual con cualquier profesional
    current_connection = PatientProfessionalConnection.objects.filter(patient=patient).first()
    
    # Para determinar si se muestra el botón de conectar o el mensaje de conexión activa
    other_connection = None
    if current_connection:
        if current_connection.professional != professional:
            other_connection = current_connection
            current_connection = None

    return render(request, 'professionals_details.html', {
        'professional': professional,
        'patient': patient,
        'current_connection': current_connection,
        'other_connection': other_connection
    })

@login_required
def clear_chat(request, user_id):
    # Asegurarse de que el usuario que hace la petición es el que corresponde al user_id o es un admin
    if request.user.id != int(user_id) and not request.user.is_superuser:
        return redirect('home')  # O alguna página de error adecuada

    # Obtener todos los mensajes del usuario especificado
    messages_to_delete = Message.objects.filter(user_id=user_id)
    
    # Eliminar los mensajes
    messages_to_delete.delete()

    # Redirigir a la vista correspondiente según el tipo de usuario
    if request.user.user_type == User.UserTypeChoices.PATIENT:
        return redirect('core:chatbot')
    elif request.user.user_type == User.UserTypeChoices.PROFESSIONAL:
        return redirect('core:chatbot-professional')
    
    # Si no se reconoce el tipo de usuario, redirige a una página de inicio o error
    return redirect('home')

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
        # Recuperar las conexiones aceptadas relacionadas con el profesional
        accepted_connections = PatientProfessionalConnection.objects.filter(professional=professional, status=ConnectionStatus.ACCEPTED)

        # Recuperar las conexiones pendientes relacionadas con el profesional
        pending_connections = PatientProfessionalConnection.objects.filter(professional=professional, status=ConnectionStatus.PENDING)
    except Professional.DoesNotExist:
        # Manejo del caso en que el usuario no tenga un perfil de profesional asociado
        accepted_connections = []
        pending_connections = []

    return render(request, 'professional/patients_list.html', {
        'patients': accepted_connections,  # Enviar conexiones aceptadas
        'pending_patients': pending_connections  # Enviar conexiones pendientes
    })


@login_required
def show_patient(request, id):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")

    professional = get_object_or_404(Professional, user=request.user)
    # Primero obtener la conexión
    connection = get_object_or_404(PatientProfessionalConnection, patient__id=id, professional=professional, status=ConnectionStatus.ACCEPTED)
    patient = connection.patient  # Aquí accedes al paciente a través de la conexión
    sessions = Session.objects.filter(patient=patient, professional=professional)

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            new_session = form.save(commit=False)
            new_session.professional = professional
            new_session.patient = patient
            new_session.save()
            return redirect('show_patient', id=id)
    else:
        form = SessionForm()

    custom_prompt = request.GET.get("custom-prompt")
    if custom_prompt:
        prompt = get_session_custom_request(patient, sessions, custom_prompt)
    else:
        prompt = get_session_recommendation(patient, sessions)

    recommendation = ask_openai([], prompt)  # Asegúrate de que esta función y su implementación son correctas

    return render(request, 'professional/patient_detail.html', {
        'patient': patient,
        'sessions': sessions,
        'form': form,
        'recommendation': recommendation
    })



#sesiones
@login_required
def create_session(request, patient_id):
    professional = Professional.objects.get(user=request.user)
    
    # Asegurarse de que existe una conexión aceptada entre el paciente y el profesional
    patient = get_object_or_404(Patient, id=patient_id)
    connection = get_object_or_404(PatientProfessionalConnection, patient=patient, professional=professional, status=ConnectionStatus.ACCEPTED)

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.professional = professional
            session.patient = patient
            session.save()
            messages.success(request, 'La sesión ha sido creada exitosamente.')
            return redirect('core:professional_patient_detail', id=patient_id)
    else:
        form = SessionForm()

    return render(request, 'professional/session_form.html', {
        'form': form,
        'patient_id': patient_id,
    })

@login_required
def edit_session(request, pk):
    session = get_object_or_404(Session, pk=pk)
    connection = get_object_or_404(PatientProfessionalConnection, patient=session.patient, professional__user=request.user, status=ConnectionStatus.ACCEPTED)

    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")

    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sesión actualizada correctamente.')
            return redirect('core:professional_patient_detail', id=session.patient.id)
    else:
        form = SessionForm(instance=session)

    return render(request, 'professional/session_form.html', {
        'form': form,
        'patient_id': session.patient.id,
        'session': session
    })

@login_required
def delete_session(request, pk):
    session = get_object_or_404(Session, pk=pk)
    connection = get_object_or_404(PatientProfessionalConnection, patient=session.patient, professional__user=request.user, status=ConnectionStatus.ACCEPTED)

    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")
    
    if request.method == 'POST':
        session.delete()
        return redirect('core:professional_patient_detail', id=session.patient.id)

    return render(request, 'professional/session_confirm_delete.html', {
        'session': session
    })


@login_required
def connectProfessional(request, professional_id):
    if request.user.user_type != User.UserTypeChoices.PATIENT:
        return HttpResponseForbidden("No autorizado")
    patient = get_object_or_404(Patient, user=request.user)

    # Verifica que no exista una conexión pendiente o aceptada
    if hasattr(patient, 'connection') and patient.connection.status in ['pending', 'accepted']:
        messages.error(request, 'Ya tienes una conexión en proceso o aceptada.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    professional = get_object_or_404(Professional, pk=professional_id)
    connection = PatientProfessionalConnection(patient=patient, professional=professional)
    connection.save()

    messages.success(request, 'Solicitud de conexión enviada.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def disconnectProfessional(request):
    user = request.user
    try:
        patient = Patient.objects.get(user=user)
        connection = PatientProfessionalConnection.objects.get(patient=patient)
    except (Patient.DoesNotExist, PatientProfessionalConnection.DoesNotExist):
        messages.error(request, 'No se encontró la conexión o el perfil del paciente.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    # Procede a eliminar la conexión
    connection.delete()

    messages.success(request, 'Desconexión del profesional realizada con éxito.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def acceptConnection(request, connection_id):
    connection = get_object_or_404(PatientProfessionalConnection, pk=connection_id, professional__user=request.user)
    connection.status = 'accepted'
    connection.save()
    messages.success(request, 'Conexión aceptada.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def rejectConnection(request, connection_id):
    connection = get_object_or_404(PatientProfessionalConnection, pk=connection_id, professional__user=request.user)
    connection.delete()
    messages.success(request, 'Conexión rechazada.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def removeConnection(request, patient_id):
    connection = get_object_or_404(PatientProfessionalConnection, patient=patient_id, professional__user=request.user)
    connection.delete()
    messages.success(request, 'Conexión removida.')
    return redirect('core:professional_patients')

@login_required
def session_list(request):
    if request.user.user_type != User.UserTypeChoices.PROFESSIONAL:
        return HttpResponseForbidden("No autorizado")

    if not request.user.is_completed:
        return redirect('complete_professional_profile')

    try:
        professional = Professional.objects.get(user=request.user)
        # Obtiene solo conexiones aceptadas para filtrar pacientes y sesiones
        connections = PatientProfessionalConnection.objects.filter(professional=professional, status=ConnectionStatus.ACCEPTED)
        patients = [connection.patient for connection in connections]
        queryset = Session.objects.filter(professional=professional, patient__in=patients).select_related('patient')

        # Filtros adicionales para la búsqueda
        patient_id = request.GET.get('patient')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        if patient_id:
            queryset = queryset.filter(patient__id=patient_id)
        if date_from:
            queryset = queryset.filter(session_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(session_date__lte=date_to)

    except Professional.DoesNotExist:
        # En caso de que no se encuentre el profesional, devolver listas vacías para mantener la integridad de la interfaz de usuario
        queryset = []
        patients = []

    return render(request, 'professional/session_list.html', {
        'sessions': queryset,
        'patients': patients  # Lista de pacientes conectados para mostrar en el filtro o en otra parte de la UI
    })

@login_required
def generate_report(request, id):
    professional = get_object_or_404(Professional, user=request.user)
    
    # Verificar la conexión aceptada antes de generar el reporte
    connection = get_object_or_404(PatientProfessionalConnection, patient__id=id, professional=professional, status=ConnectionStatus.ACCEPTED)
    patient = connection.patient
    sessions = Session.objects.filter(patient=patient, professional=professional)

    # Suponiendo que get_session_csv_report y ask_openai están correctamente definidos
    prompt = get_session_csv_report(patient, sessions)
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
    response['Content-Disposition'] = f'attachment; filename="reporte-{patient.user.username}.csv"'

    return response


