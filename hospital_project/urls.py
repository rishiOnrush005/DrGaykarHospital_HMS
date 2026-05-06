from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Staff Management
    path('staff/', account_views.staff_list, name='staff_list'),
    path('staff/create/', account_views.create_staff, name='create_staff'),
    path('staff/delete/<int:pk>/', account_views.delete_staff, name='delete_staff'),
    
    path('', include('dashboard.urls')),
    path('patients/', include('patients.urls')),
    path('visits/', include('visits.urls')),
    path('backup/', include('backup.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
