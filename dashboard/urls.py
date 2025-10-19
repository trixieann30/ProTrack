from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard URLs
    path('', views.dashboard, name='dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('training/', views.training, name='training'),
    path('certifications/', views.certifications, name='certifications'),
    
    # Settings URLs
    path('settings/', views.settings, name='settings'),
    path('settings/profile/', views.profile_settings, name='profile_settings'),
    path('settings/password/', views.change_password, name='change_password'),
    
    # Admin CRUD URLs
    path('admin/users/', views.admin_users_list, name='admin_users_list'),
    path('admin/users/create/', views.admin_user_create, name='admin_user_create'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('admin/users/<int:user_id>/toggle-status/', views.admin_user_toggle_status, name='admin_user_toggle_status'),
]