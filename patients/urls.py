from django.urls import path
from . import views

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('register/', views.patient_register, name='patient_register'),
    path('import/', views.import_patients_csv, name='import_patients_csv'),
    path('export/', views.export_patients_csv, name='export_patients_csv'),
    path('<uuid:uuid>/', views.patient_detail, name='patient_detail'),
]
