from django.urls import path
from . import views

urlpatterns = [
    path('record/<uuid:patient_uuid>/', views.record_visit, name='record_visit'),
    path('complete/<uuid:visit_uuid>/', views.complete_visit, name='complete_visit'),
]
