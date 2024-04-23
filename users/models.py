from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
from tinymce.models import HTMLField


class User(AbstractBaseUser, PermissionsMixin):
    """clase para generar mi modelo personalizado de usuarios"""

    class GenderChoices(models.TextChoices):
        MAN = "1", "hombre"
        WOMAN = "2", "mujer"
        
    class UserTypeChoices(models.TextChoices):
        PATIENT = "P", "Paciente"
        PROFESSIONAL = "PR", "Profesional"

    username = models.CharField("nombre de usuario", max_length=50, unique=True)
    full_name = models.CharField("nombre completo", max_length=150)
    gender = models.CharField(
        "género", max_length=1, choices=GenderChoices.choices, blank=True, null=True
    )
    email = models.EmailField("correo electrónico", max_length=254, unique=True)
    phone_number = models.CharField("Celular",max_length=20, blank=True)
    city = models.ManyToManyField('core.CityOption', related_name='users', blank=True)
    birthday = models.DateField("Fecha de nacimiento",null=True, blank=True)
    is_staff = models.BooleanField("staff", default=False)
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
     # Permiso para que el campo sea null en la base de datos
    user_type = models.CharField(
        "tipo de usuario", max_length=2, choices=UserTypeChoices.choices, null=True, blank=True
    )

    USERNAME_FIELD = "username"

    # para que la terminal nos pida estos datos al crear un superuser
    REQUIRED_FIELDS = ['email', 'full_name']
    objects = UserManager()
    groups = models.ManyToManyField(
        verbose_name='groups',
        to='auth.Group',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="account", 
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        verbose_name='user permissions',
        to='auth.Permission',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="account", 
        related_query_name="user",
    )


class Post(models.Model):
    title = models.CharField(max_length=200)
    body = HTMLField()  # Usar HTMLField en lugar de TextField
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    featured_image = models.ImageField(upload_to='posts/', blank=True, null=True) 

    def __str__(self):
        return self.title
