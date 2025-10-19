from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
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
]