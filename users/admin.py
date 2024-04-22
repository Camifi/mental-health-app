from django.contrib import admin
from django.db import models
from .models import Post, User  # Asumiendo que realmente quieres registrar User desde tu modelo local
from tinymce.widgets import TinyMCE

# Definición de PostAdmin
class PostAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE()},  # Asegúrate de que tu modelo usa TextField donde quieres aplicar TinyMCE
    }

# Registra el modelo User si es necesario
admin.site.register(User)

# Registra el modelo Post usando la clase PostAdmin
admin.site.register(Post, PostAdmin)