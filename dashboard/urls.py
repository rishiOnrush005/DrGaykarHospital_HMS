from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('set-language/', views.set_language_pref, name='set_language_pref'),
]
