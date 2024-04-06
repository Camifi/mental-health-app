from .models import Professional

FILL_THE_PATIENT_DATA_PROMPT = (
        "Eres un bot programado para asistir usuarios en una web de consultas psicológicas, debes ser amable y empático con los usuarios y no salirte de contexto.\n\n"
        "Cuando un usuario te escriba, te presentarás de la siguiente manera:\n\n"
       "Hola, soy un asistente virtual. Estoy aquí para ayudarte con la búsqueda de un profesional de la salud mental.\n"
        "Este proceso es solo un paso inicial y no sustituye una consulta profesional.\n"
        "\"Si estás list@ para comenzar, simplemente responde 'Sí', y procederemos con las ciertas "
        "preguntas.\n\n"
        "\"Espera a que el usuario responda si antes de enviar las preguntas, y haz solo una pregunta por mensaje,además de que debes mostrar empatía \n\n"
        "\"Espera a que el usuario responda cada pregunta, verifica que es una respuesta válida para la pregunta en cuestión\n\n"
        "\"Si el usuario dio una respuesta inválida vuelve a preguntar.Una vez que responda de manera válida continua con la "
        "siguiente pregunta en otro mensaje\n\n"
        "\"Repite el procedimiento con cada pregunta.Esta son las preguntas:\n\n"
        "1. ¿Recibió terapia anteriormente en psicología o psiquiatría?\n"
        "- En caso de que diga 'Sí', la siguiente pregunta es: ¿Podrías comentarnos el nombre de tu médico de cabecera?\n\n"
        "2. Motivo de la consulta.\n\n"
        "3. Descripción de síntomas.\n\n"
        "4. Objetivos de la terapia.\n\n"
        "5. Preferencia horaria para las sesiones.\n\n"
        "6. Preferencia de terapeuta, ¿prefieres hombre ,mujer o no tienes preferencia?\n\n"
        "Luego de que responda satisfactoriamente la pregunta 6 NO RESPONDAS NADA, solo responde con 'CONFIRMED' así tal cual en "
        "mayúsculas."
        )

CREATE_A_JSON_PATIENT_PROMPT = (
        "Elabora un JSON con la siguiente estructura en base a las respuestas del usuario citados abajo: {"
        "\"recibio_terapia\": \"*respuesta a si recibió terapia anteriormente\", "
        "\"medico_cabecera\": \"*respuesta al nombre del médico de cabecera, si aplica\", "
        "\"motivo_consulta\": \"*respuesta al motivo de la consulta\", "
        "\"descripcion_sintomas\": \"*respuesta a la descripción de síntomas\", "
        "\"objetivos_terapia\": \"*respuesta a los objetivos de la terapia\", "
        "\"preferencia_horaria\": \"*respuesta a la preferencia horaria\", "
        "\"preferencia_terapeuta\": \"*respuesta a la preferencia de género del terapeuta, 'F' si femenino, 'M' si masculino, "
         "o 'N' si no tiene preferencia \""
        "}. \n\n"
)

SUGGEST_A_PROFESSIONAL_PROMPT = (
        "Recomienda hasta 3 profesionales de nuestra lista, basado en sus parámetros. "
        "El que consideremos que tenga mayor compatibilidad con las respuestas del usuario. "
        "La recomendación debe ser en el siguiente formato: \n\n"
        "-Nombre: \n\n"
        "-Por qué se lo recomendamos: \n\n"
        "-Enlace a su perfil: \n\n"
        "Nuestro listado de profesionales y sus detalles son: "
)

def get_initial_prompt(prompt_type):
    if prompt_type == 1:
        return FILL_THE_PATIENT_DATA_PROMPT
    if prompt_type == 2:
        return CREATE_A_JSON_PATIENT_PROMPT
    if prompt_type == 3:
        professionals = Professional.objects.all()
        return SUGGEST_A_PROFESSIONAL_PROMPT + get_professional_list_formatted(professionals)

def get_patient_completed_prompt(patient, user):
    initial = (f"Eres un bot programado para asistir usuarios en una web de consultas psicológicas, debes ser amable y empático con los usuarios y no salirte de contexto.\n\n"
            f"El usuario al que vas a atender se llama {user.full_name} y dale soporte en todo lo que necesite."
            f"La fecha de cumpleaños del usuario  {user.birthday} su edad es el anio de nacimiento - el anio actual(2024) "
            f"sdad {user.city}"
            # f"sdad {user.full_name}"
            "Si el usuario solicita que le recomendemos un profesional"
            "recomienda de la siguiente lista:\n"
            )
    professionals = Professional.objects.all()
    return initial + get_professional_list_formatted(professionals)

def get_professional_list_formatted(professional_list):
    formatted_list = []
    
    for professional in professional_list:
        full_name = professional.user.full_name  
        gender = professional.user.get_gender_display()  
        
        # Obteniendo disponibilidad
        availability_list = professional.availability.all()
        availability_str = ", ".join([option.name for option in availability_list])
        
        # Construyendo el string para este profesional
        professional_str = f"""
            Profesional: {full_name}
            Sexo: {gender}
            Título: {professional.title}
            Especialización: {professional.specialization}
            Certificaciones: {professional.certifications_or_courses}
            Métodos de terapia: {professional.therapeutic_approaches}
            Grupo demográfico que atiende: {professional.demographic_groups_served}
            Modalidad de terapia: {professional.get_session_modalities_display()}
            Disponibilidad: {availability_str}
            Ciudad donde brinda atención: {professional.city_served}
            Breve biografía: {professional.biography}
            Enlace: http://127.0.0.1:8000/professionals/{professional.slug}
            """
        formatted_list.append(professional_str)
    
    return "\n".join(formatted_list)