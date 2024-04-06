
from django.contrib import admin
from django.urls import include, path
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.homepage, name='home'), 
    path('signup/', user_views.signup, name='signup'),
    path('signin/', user_views.signin, name='signin'),
    path('dashboard/', user_views.dashboard, name='dashboard'),
    path('aviso/', user_views.aviso, name='aviso'),
    path('logout/', user_views.signout, name='logout'),
    path('select_user_type/', user_views.select_user_type, name='select_user_type'),
    path('profile/update/', user_views.complete_user_common_info, name='complete_user_common_info'),
    path('profile/professional/update/', user_views.complete_professional_profile, name='complete_professional_profile'),
    path('delete_account/', user_views.UserDeleteView.as_view(), name='delete_account'),    
    path('', include(('core.urls', 'core'), namespace='core')),  # Incluye las URLs de 'core' con espacio de nombres
]
