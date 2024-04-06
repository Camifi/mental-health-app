from .models import Message, Patient
import openai
import json
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

def ask_openai(chats, initial_message):
    instruction = {
    "role": "system",
    "content": initial_message
    }

    messages_for_openai = [
        {
            "role": "user" if chat else "assistant",
            "content": chat.content
        }
        for chat in chats
    ]

    messages_for_openai.insert(0, instruction)

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_for_openai,
        )
        # Asegúrate de acceder correctamente al contenido de la respuesta.
        answer = completion.choices[0].message['content'].strip()
        return answer
    except Exception as e:
        print(f"Error al solicitar la completación: {e}")
        return "Lo siento, hubo un error al procesar tu solicitud."
    
    
def create_patient(response_content, my_user):
    
    try:
        user_info = json.loads(response_content)
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}") 
        return False

    patient, created = Patient.objects.get_or_create(user=my_user)
    
    # Actualización del perfil del paciente con la información proporcionada
    patient.primary_care_physician = user_info.get('medico_cabecera', patient.primary_care_physician)
    patient.previous_therapy_experience = user_info.get('recibio_terapia', patient.previous_therapy_experience)
    patient.reason_for_therapy = user_info.get('motivo_consulta', patient.reason_for_therapy)
    patient.therapy_schedule_preference = user_info.get('preferencia_horaria', patient.therapy_schedule_preference)
    patient.symptoms_description = user_info.get('descripcion_sintomas', patient.symptoms_description)
    patient.therapy_goals = user_info.get('objetivos_terapia', patient.therapy_goals)
    patient.therapist_gender_preference = user_info.get('preferencia_terapeuta', patient.therapist_gender_preference)
    
    patient.save()
    
    return True
   


