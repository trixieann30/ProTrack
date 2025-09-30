from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('training/', views.training, name='training'),
    path('certifications/', views.certifications, name='certifications'),
]