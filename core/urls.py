from django.urls import path
from django.conf.urls.static import static
from core import views
from mental_health_app import settings

urlpatterns = [
    
    path('chatbot/',views.chatbot, name='chatbot'),
    path('professional-chatbot/',views.chatbot_profesional, name='chatbot-professional'),
     path('professional/welcome', views.welcome_professional, name='professional_home'),
     
    path('welcome/', views.dashboard_patient, name='patient_home'),
    path('professionals/', views.list_professionals, name='list_professionals'),
    path('professionals/<slug:slug>/', views.professional_detail, name='professional_detail'),
    path('clear-chat/<int:user_id>/', views.clear_chat, name='clear_chat'),
    

   
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)