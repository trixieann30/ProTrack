# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.db.models import Count
# from accounts.models import CustomUser
# from django.core.exceptions import PermissionDenied

# @login_required
# def dashboard(request):
#     user = request.user
    
#     if user.user_type == 'admin':
#     # Dashboard statistics
#         context = {
#             'user': user,
#             'total_users': CustomUser.objects.count(),
#             'total_students': CustomUser.objects.filter(user_type='student').count(),
#             'total_employees': CustomUser.objects.filter(user_type='employee').count(),
#             'total_admins': CustomUser.objects.filter(user_type='admin').count(),
#         }
#      elif user.user_type in ['student', 'employee']:
#         # Regular users see limited statistics
#         context = {
#             'user': user,
#             'total_users': None,  # Hidden from regular users
#             'total_students': None,
#             'total_employees': None,
#             'total_admins': None,
#         }
#     else:
#         # Invalid user type - deny access
#         raise PermissionDenied

#     return render(request, 'dashboard/dashboard.html', context)

# @login_required
# def training(request):
#     return render(request, 'dashboard/training.html')

# @login_required
# def certifications(request):
#     return render(request, 'dashboard/certifications.html')


# # Create your views here.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser
from .models import TrainingCourse, TrainingCategory, TrainingSession, Enrollment
from django.http import JsonResponse
from django.contrib import messages
from django.db import models
from django.utils import timezone
def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    """Admin dashboard - only accessible by superusers"""
    user = request.user
    
    # Admins see all statistics
    context = {
        'user': user,
        'total_users': CustomUser.objects.count(),
        'total_students': CustomUser.objects.filter(user_type='student').count(),
        'total_employees': CustomUser.objects.filter(user_type='employee').count(),
        'total_admins': CustomUser.objects.filter(is_superuser=True).count(),
        'recent_users': CustomUser.objects.order_by('-created_at')[:5],
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def user_dashboard(request):
    """User dashboard - for regular users (students and employees)"""
    user = request.user
    
    # Redirect superusers to admin dashboard
    if user.is_superuser:
        return redirect('dashboard:admin_dashboard')
    
    # Regular users see their own statistics
    context = {
        'user': user,
    }
    
    return render(request, 'dashboard/user_dashboard.html', context)

@login_required
def dashboard(request):
    """Main dashboard router - redirects to appropriate dashboard"""
    if request.user.is_superuser:
        return redirect('dashboard:admin_dashboard')
    else:
        return redirect('dashboard:user_dashboard')

@login_required
def training(request):
    # RBAC: Check if user has access to training
    if request.user.user_type not in ['student', 'employee', 'admin']:
        raise PermissionDenied
    return render(request, 'dashboard/training.html')

@login_required
def certifications(request):
    # RBAC: Check if user has access to certifications
    if request.user.user_type not in ['student', 'employee', 'admin']:
        raise PermissionDenied
    return render(request, 'dashboard/certifications.html')


@login_required
def training_catalog(request):
    """Display all available training courses with search and filters"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    level_filter = request.GET.get('level', '')
    status_filter = request.GET.get('status', 'active')
    
    # Base queryset
    courses = TrainingCourse.objects.filter(status=status_filter)
    
    # Apply search
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instructor__icontains=search_query)
        )
    
    # Apply category filter
    if category_filter:
        courses = courses.filter(category_id=category_filter)
    
    # Apply level filter
    if level_filter:
        courses = courses.filter(level=level_filter)
    
    # Annotate with enrollment counts
    courses = courses.annotate(enrollment_count=Count('enrollments'))
    
    # Get all categories for filter dropdown
    categories = TrainingCategory.objects.all()
    
    # Get user's enrollments
    user_enrollments = set(
        Enrollment.objects.filter(user=request.user)
        .values_list('course_id', flat=True)
    )
    
    context = {
        'courses': courses,
        'categories': categories,
        'user_enrollments': user_enrollments,
        'search_query': search_query,
        'category_filter': category_filter,
        'level_filter': level_filter,
        'total_courses': courses.count(),
    }
    
    return render(request, 'dashboard/training_catalog.html', context)


@login_required
def course_detail(request, course_id):
    """Display detailed information about a specific course"""
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    # Check if user is already enrolled
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=course)
        is_enrolled = True
    except Enrollment.DoesNotExist:
        enrollment = None
        is_enrolled = False
    
    # Get upcoming sessions
    from django.utils import timezone
    upcoming_sessions = course.sessions.filter(
        start_date__gte=timezone.now().date()
    ).order_by('start_date')[:5]
    
    # Get recent enrollments (for admin view)
    recent_enrollments = course.enrollments.select_related('user').order_by('-enrolled_date')[:10]
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'is_enrolled': is_enrolled,
        'upcoming_sessions': upcoming_sessions,
        'recent_enrollments': recent_enrollments,
        'can_enroll': not course.is_full and not is_enrolled,
    }
    
    return render(request, 'dashboard/course_detail.html', context)


@login_required
def enroll_course(request, course_id):
    """Handle user self-enrollment in a course"""
    if request.method != 'POST':
        return redirect('dashboard:course_detail', course_id=course_id)
    
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    # Check if course is full
    if course.is_full:
        messages.error(request, 'This course is currently full.')
        return redirect('dashboard:course_detail', course_id=course_id)
    
    # Check if already enrolled
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.warning(request, 'You are already enrolled in this course.')
        return redirect('dashboard:course_detail', course_id=course_id)
    
    # Get selected session if provided
    session_id = request.POST.get('session_id')
    session = None
    if session_id:
        session = get_object_or_404(TrainingSession, id=session_id, course=course)
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        user=request.user,
        course=course,
        session=session,
        status='enrolled',  # Self-enrollment is auto-approved
    )
    
    messages.success(
        request,
        f'Successfully enrolled in "{course.title}"! Check your training dashboard for details.'
    )
    
    return redirect('dashboard:my_training')


@login_required
def my_training(request):
    """Display user's enrolled courses and progress"""
    # Get user's enrollments
    enrollments = Enrollment.objects.filter(user=request.user).select_related(
        'course', 'session'
    ).order_by('-enrolled_date')
    
    # Categorize enrollments
    active_enrollments = enrollments.filter(status__in=['enrolled', 'in_progress'])
    completed_enrollments = enrollments.filter(status='completed')
    pending_enrollments = enrollments.filter(status='pending')
    
    # Calculate statistics
    total_hours = sum(e.course.duration_hours for e in completed_enrollments)
    avg_score = enrollments.filter(score__isnull=False).aggregate(
        avg=models.Avg('score')
    )['avg'] or 0
    
    context = {
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'pending_enrollments': pending_enrollments,
        'total_completed': completed_enrollments.count(),
        'total_hours': total_hours,
        'avg_score': round(avg_score, 1),
        'in_progress_count': active_enrollments.count(),
    }
    
    return render(request, 'dashboard/my_training.html', context)


@login_required
def cancel_enrollment(request, enrollment_id):
    """Allow user to cancel their enrollment"""
    if request.method != 'POST':
        return redirect('dashboard:my_training')
    
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        user=request.user
    )
    
    # Only allow cancellation if not completed
    if enrollment.status == 'completed':
        messages.error(request, 'Cannot cancel a completed course.')
        return redirect('dashboard:my_training')
    
    enrollment.cancel()
    messages.success(request, f'Enrollment in "{enrollment.course.title}" has been cancelled.')
    
    return redirect('dashboard:my_training')


# Admin views for assigning training
@login_required
def assign_training(request):
    """Admin view to assign training to users"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to assign training.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        course_id = request.POST.get('course_id')
        session_id = request.POST.get('session_id')
        
        if not user_ids or not course_id:
            messages.error(request, 'Please select users and a course.')
            return redirect('dashboard:assign_training')
        
        course = get_object_or_404(TrainingCourse, id=course_id)
        session = None
        if session_id:
            session = get_object_or_404(TrainingSession, id=session_id)
        
        # Create enrollments
        created_count = 0
        skipped_count = 0
        
        for user_id in user_ids:
            user = get_object_or_404(CustomUser, id=user_id)
            
            # Check if already enrolled
            if Enrollment.objects.filter(user=user, course=course).exists():
                skipped_count += 1
                continue
            
            Enrollment.objects.create(
                user=user,
                course=course,
                session=session,
                status='enrolled',
                assigned_by=request.user,
            )
            created_count += 1
        
        messages.success(
            request,
            f'Successfully assigned {created_count} user(s) to "{course.title}". '
            f'{skipped_count} user(s) were already enrolled.'
        )
        
        return redirect('dashboard:assign_training')
    
    # GET request - show assignment form
    users = CustomUser.objects.filter(user_type__in=['student', 'employee']).order_by('username')
    courses = TrainingCourse.objects.filter(status='active').order_by('title')
    
    context = {
        'users': users,
        'courses': courses,
    }
    
    return render(request, 'dashboard/assign_training.html', context)


@login_required
def get_course_sessions(request, course_id):
    """API endpoint to get sessions for a specific course"""
    course = get_object_or_404(TrainingCourse, id=course_id)
    sessions = course.sessions.filter(
        start_date__gte=timezone.now().date()
    ).values('id', 'session_name', 'start_date', 'location')
    
    return JsonResponse(list(sessions), safe=False)