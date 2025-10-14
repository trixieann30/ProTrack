from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('training/', views.training, name='training'),
    path('certifications/', views.certifications, name='certifications'),
]