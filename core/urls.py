from django.urls import path
from django.conf.urls.static import static
from core import views
from mental_health_app import settings

urlpatterns = [
    # rutas para patient
    path('welcome/', views.dashboard_patient, name='patient_home'),
    path('chatbot/',views.chatbot, name='chatbot'),
    path('clear-chat/<int:user_id>/', views.clear_chat, name='clear_chat'),
    path('professionals/', views.list_professionals, name='list_professionals'),
    path('professionals/<slug:slug>/', views.professional_detail, name='professional_detail'),
    path('connect/<int:professional_id>/', views.connectProfessional, name='connect_professional'),
    path('disconnect/', views.disconnectProfessional, name='disconnect_professional'),


    # rutas para professional
    path('professional/welcome/', views.welcome_professional, name='professional_home'),
    path('professional/chatbot/',views.chatbot_profesional, name='chatbot-professional'),
    path('professional/patients/', views.list_patients, name='professional_patients'),
    path('professional/patients/<int:id>/', views.show_patient, name='professional_patient_detail'),
    path('professional/patients/<int:id>/report/', views.generate_report, name="patient_report"),
    path('professional/connection/accept/<int:connection_id>/', views.acceptConnection, name='accept_connection'),
    path('professional/connection/reject/<int:connection_id>/', views.rejectConnection, name='reject_connection'),

    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/<int:patient_id>/', views.create_session, name='create_session'),
    path('sessions/edit/<int:pk>/', views.edit_session, name='edit_session'),  # Editar una sesión existente
    path('sessions/delete/<int:pk>/', views.delete_session, name='delete_session'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)