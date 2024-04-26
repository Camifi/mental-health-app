from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db.models import Max
from django.db.models.functions import Length

# Esto obtendrá el modelo de usuario personalizado
User = get_user_model()

class AvailabilityOption(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name
class GroupOption(models.Model):
    name = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return self.name

# Modelo CityOption
class CityOption(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Professional(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professional_profile')
    title = models.CharField(_("Título Obtenido"), max_length=255, blank=True)
    specialization = models.CharField(_("Especialización"), max_length=255, blank=True)
    certifications_or_courses = models.TextField(_("Certificaciones o Cursos Adicionales"), blank=True, null=True)
    therapeutic_approaches = models.TextField(_("Métodos utilizados en la terapia"))
    demographic_groups_served = models.ManyToManyField(GroupOption, related_name='professionals')
    session_modalities = models.CharField(_("Modalidad de la terapia"), max_length=50, choices=(('In-person', 'Presencial'), ('Virtual', 'Virtual'), ('Both', 'Ambos')))
    availability = models.ManyToManyField(AvailabilityOption, related_name='professional')
    city_served = models.ManyToManyField(CityOption, related_name='professional')
    biography = models.TextField(_("Breve biografía"), max_length=256, blank=True)
    profile_image = models.ImageField(_("Foto de perfil"), upload_to='profiles/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.user.full_name)
            self.slug = original_slug
            queryset = Professional.objects.all().filter(slug__startswith=original_slug)
            if queryset.exists():
                max_length = queryset.aggregate(max_length=Max(Length('slug')))['max_length']
                max_slugs = queryset.filter(slug__length=max_length)
                next_number = max_slugs.aggregate(max_number=Max('slug__int'))['max_number'] + 1
                self.slug = f'{original_slug}-{next_number}'
        super(Professional, self).save(*args, **kwargs)

     # Este es el método __str__ que debes añadir:
    def __str__(self):
        # Asegúrate de que 'full_name' es el campo correcto en tu modelo de User.
        # Si usas el modelo User predeterminado de Django, podría ser 'username' o 'first_name'.
        return self.user.full_name
    

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    primary_care_physician = models.CharField(_("Médico de Cabecera"), max_length=255, blank=True, null=True)
    previous_therapy_experience = models.TextField(_("Realizo terapia anteriormente"), blank=True, null=True)
    reason_for_therapy = models.TextField(_("Motivo de la consulta"))
    therapy_schedule_preference = models.CharField(_("Preferencia horaria"), max_length=255)
    symptoms_description = models.TextField(_("Descripcion de Síntomas"))
    therapy_goals = models.TextField(_("Objetivos de la terapia"))
    THERAPIST_GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('N', 'No tengo preferencia'),  # Agrega esta nueva opción
    ]

    therapist_gender_preference = models.CharField(
        _("Preferencia de Terapeuta"),
        max_length=1,  # Considera cambiar esto si el identificador de tu nueva opción es más largo
        choices=THERAPIST_GENDER_CHOICES,
        blank=True)
    def __str__(self):
        # Asegúrate de que 'full_name' es el campo correcto en tu modelo de User.
        # Si usas el modelo User predeterminado de Django, podría ser 'username' o 'first_name'.
        return self.user.full_name


class ConnectionStatus(models.TextChoices):
    PENDING = 'pending', 'Pendiente'
    ACCEPTED = 'accepted', 'Aceptado'


class PatientProfessionalConnection(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='connection')
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='connections')
    status = models.CharField(
        max_length=20,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.PENDING
    )

    def __str__(self):
        return f"{self.patient.user.full_name} - {self.professional.user.full_name} - {self.status}"


class Session(models.Model):
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='sessions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField(_("Fecha de la sesión"))
    objectives = models.TextField(_("Objetivo trabajado"))
    difficulties = models.TextField(_("Dificultades"), blank=True, null=True)

    def __str__(self):
      
        patient_name = self.patient.user.username  
        profesional_name = self.professional.user.full_name
        return f"{self.session_date} - {patient_name} - {profesional_name}"


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(max_length=256)
    created_at = models.DateTimeField(default=timezone.now)
    is_from_user = models.BooleanField(default=True)  # Indica si el mensaje es del usuario o del bot

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

