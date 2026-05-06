from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.backup_manager, name='backup_manager'),
    path('restore/', views.restore_database, name='restore_database'),
    path('verify/', views.verify_pin, name='verify_pin'),
]
