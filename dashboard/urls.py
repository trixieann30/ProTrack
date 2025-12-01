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
    path('certifications/approve/<int:certificate_id>/', views.approve_certificate, name='approve_certificate'),
    path('training/my-training/', views.my_training, name='my_training'),
    path('training/cancel/<int:enrollment_id>/', views.cancel_enrollment, name='cancel_enrollment'),
    path('training/enrollment/<int:enrollment_id>/material/<int:material_id>/complete/', views.mark_material_complete, name='mark_material_complete'),
    path('training/quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    
    # Admin: Assign training
    path('training/assign/', views.assign_training, name='assign_training'),
    path('api/course/<int:course_id>/sessions/', views.get_course_sessions, name='get_course_sessions'),
    path('certifications/', views.certifications, name='certifications'),
    
    # Reports (US-03)
    path('reports/', views.reports, name='reports'),

    # Calendar (US-01A)
    path('calendar/', views.calendar, name='calendar'),
    path('api/calendar-events/', views.get_calendar_events, name='calendar_events'),
    path('api/enrollment/update-completion/', views.update_enrollment_completion, name='update_enrollment_completion'),
    
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
    path('training/course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('training/course/<int:course_id>/archive/', views.archive_course, name='archive_course'),
    path('training/archive/', views.archive_training, name='archive_training'),
    path('dashboard/training/archived/', views.archived_courses, name='archived_courses'),
    path('training/restore/<int:course_id>/', views.restore_course, name='restore_course'),
    path('training/course/<int:course_id>/upload/', views.upload_material, name='upload_material'),
    path('training/material/<int:material_id>/delete/', views.delete_material, name='delete_material'),
    path('certificate/<int:certificate_id>/download/', views.download_certificate, name='download_certificate'),
    path('training/course/<int:course_id>/download-all/', views.download_all_materials, name='download_all_materials'),
    
    # Admin: Quiz Management
    path('admin/quizzes/material/<int:material_id>/manage/', views.manage_quiz, name='manage_quiz'),

    # Notification URLs
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('api/notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),

]
