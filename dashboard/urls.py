from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard URLs
    path('', views.dashboard, name='dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    # Training catalog and enrollment
    path('training/', views.training_catalog, name='training'),
    path('training/catalog/', views.training_catalog, name='training_catalog'),
    path('training/course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('training/enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('training/my-training/', views.my_training, name='my_training'),
    path('training/cancel/<int:enrollment_id>/', views.cancel_enrollment, name='cancel_enrollment'),
    
    # Admin: Assign training
    path('training/assign/', views.assign_training, name='assign_training'),
    path('api/course/<int:course_id>/sessions/', views.get_course_sessions, name='get_course_sessions'),
    path('certifications/', views.certifications, name='certifications'),
    
    # Reports (US-03)
    path('reports/', views.reports, name='reports'),
    
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

    # Admin: Assign & Create training
    path('training/assign/', views.assign_training, name='assign_training'),
    path('training/create/', views.create_training, name='create_training'),
    path('training/course/<int:course_id>/archive/', views.archive_course, name='archive_course'),
    path('training/archive/', views.archive_training, name='archive_training'),
]