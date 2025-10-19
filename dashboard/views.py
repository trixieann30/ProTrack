from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from accounts.models import CustomUser
from .models import TrainingCourse, TrainingCategory, TrainingSession, Enrollment


def is_superuser(user):
    return user.is_superuser


# ============ DASHBOARD VIEWS ============

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
    return render(request, 'dashboard/training.html')


@login_required
def certifications(request):
    return render(request, 'dashboard/certifications.html')


# ============ TRAINING VIEWS ============

@login_required
def training_catalog(request):
    """Display all available training courses"""
    courses = TrainingCourse.objects.filter(status='active').select_related('category')
    categories = TrainingCategory.objects.all()
    
    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    # Filter by level if provided
    level = request.GET.get('level')
    if level:
        courses = courses.filter(level=level)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instructor__icontains=search_query)
        )
    
    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': category_id,
        'selected_level': level,
        'search_query': search_query,
    }
    return render(request, 'dashboard/training_catalog.html', context)


@login_required
def course_detail(request, course_id):
    """Display detailed information about a specific course"""
    course = get_object_or_404(TrainingCourse, id=course_id)
    sessions = course.sessions.filter(start_date__gte=timezone.now().date())
    
    # Check if user is already enrolled
    is_enrolled = Enrollment.objects.filter(
        user=request.user,
        course=course,
        status__in=['pending', 'enrolled', 'in_progress']
    ).exists()
    
    context = {
        'course': course,
        'sessions': sessions,
        'is_enrolled': is_enrolled,
    }
    return render(request, 'dashboard/course_detail.html', context)


@login_required
def enroll_course(request, course_id):
    """Enroll user in a training course"""
    if request.method == 'POST':
        course = get_object_or_404(TrainingCourse, id=course_id)
        session_id = request.POST.get('session_id')
        
        # Check if course is full
        if course.is_full:
            messages.error(request, 'This course is currently full.')
            return redirect('dashboard:course_detail', course_id=course_id)
        
        # Check if already enrolled
        existing_enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status__in=['pending', 'enrolled', 'in_progress']
        ).first()
        
        if existing_enrollment:
            messages.warning(request, 'You are already enrolled in this course.')
            return redirect('dashboard:my_training')
        
        # Create enrollment
        session = None
        if session_id:
            session = TrainingSession.objects.filter(id=session_id).first()
        
        Enrollment.objects.create(
            user=request.user,
            course=course,
            session=session,
            status='enrolled'
        )
        
        messages.success(request, f'Successfully enrolled in {course.title}!')
        return redirect('dashboard:my_training')
    
    return redirect('dashboard:training_catalog')


@login_required
def my_training(request):
    """Display user's enrolled training courses"""
    enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related('course', 'session').order_by('-enrolled_date')
    
    context = {
        'enrollments': enrollments,
    }
    return render(request, 'dashboard/my_training.html', context)


@login_required
def cancel_enrollment(request, enrollment_id):
    """Cancel a training enrollment"""
    if request.method == 'POST':
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
        
        if enrollment.status in ['completed', 'cancelled']:
            messages.warning(request, 'Cannot cancel this enrollment.')
        else:
            enrollment.cancel()
            messages.success(request, 'Enrollment cancelled successfully.')
        
        return redirect('dashboard:my_training')
    
    return redirect('dashboard:my_training')


# ============ ADMIN TRAINING MANAGEMENT ============

@login_required
@user_passes_test(is_superuser)
def assign_training(request):
    """Admin view to assign training to users"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        course_id = request.POST.get('course_id')
        session_id = request.POST.get('session_id')
        
        try:
            user = CustomUser.objects.get(id=user_id)
            course = TrainingCourse.objects.get(id=course_id)
            session = TrainingSession.objects.get(id=session_id) if session_id else None
            
            # Check if already enrolled
            existing = Enrollment.objects.filter(user=user, course=course).first()
            if existing:
                messages.warning(request, f'{user.username} is already enrolled in {course.title}.')
            else:
                Enrollment.objects.create(
                    user=user,
                    course=course,
                    session=session,
                    status='enrolled',
                    assigned_by=request.user
                )
                messages.success(request, f'Successfully assigned {course.title} to {user.username}.')
        except Exception as e:
            messages.error(request, f'Error assigning training: {str(e)}')
        
        return redirect('dashboard:admin_dashboard')
    
    # GET request - show assignment form
    users = CustomUser.objects.filter(is_active=True)
    courses = TrainingCourse.objects.filter(status='active')
    
    context = {
        'users': users,
        'courses': courses,
    }
    return render(request, 'dashboard/assign_training.html', context)


@login_required
def get_course_sessions(request, course_id):
    """API endpoint to get sessions for a specific course"""
    sessions = TrainingSession.objects.filter(
        course_id=course_id,
        start_date__gte=timezone.now().date()
    ).values('id', 'session_name', 'start_date', 'end_date', 'location', 'is_online')
    
    return JsonResponse(list(sessions), safe=False)


# ============ SETTINGS VIEWS ============

@login_required
def settings(request):
    """Main settings page"""
    return render(request, 'dashboard/settings.html')


@login_required
def profile_settings(request):
    """User profile settings"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('dashboard:profile_settings')
    
    return render(request, 'dashboard/profile_settings.html')


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('dashboard:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'dashboard/change_password.html', {'form': form})


# ============ ADMIN USER MANAGEMENT VIEWS ============

@login_required
@user_passes_test(is_superuser)
def admin_users_list(request):
    """List all users with pagination and filtering"""
    users = CustomUser.objects.all().order_by('-created_at')
    
    # Filter by user type
    user_type = request.GET.get('user_type')
    if user_type:
        if user_type == 'admin':
            users = users.filter(is_superuser=True)
        else:
            users = users.filter(user_type=user_type)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'user_type': user_type,
    }
    return render(request, 'dashboard/admin_users_list.html', context)


@login_required
@user_passes_test(is_superuser)
def admin_user_detail(request, user_id):
    """View detailed information about a user"""
    user = get_object_or_404(CustomUser, id=user_id)
    enrollments = Enrollment.objects.filter(user=user).select_related('course')
    
    context = {
        'viewed_user': user,
        'enrollments': enrollments,
    }
    return render(request, 'dashboard/admin_user_detail.html', context)


@login_required
@user_passes_test(is_superuser)
def admin_user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_type = request.POST.get('user_type')
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                is_superuser=is_superuser,
                is_staff=is_superuser
            )
            messages.success(request, f'User {username} created successfully.')
            return redirect('dashboard:admin_user_detail', user_id=user.id)
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    return render(request, 'dashboard/admin_user_create.html')


@login_required
@user_passes_test(is_superuser)
def admin_user_edit(request, user_id):
    """Edit user information"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.user_type = request.POST.get('user_type', user.user_type)
        
        # Only allow changing superuser status if not editing self
        if user.id != request.user.id:
            user.is_superuser = request.POST.get('is_superuser') == 'on'
            user.is_staff = user.is_superuser
        
        user.save()
        messages.success(request, 'User updated successfully.')
        return redirect('dashboard:admin_user_detail', user_id=user.id)
    
    context = {
        'viewed_user': user,
    }
    return render(request, 'dashboard/admin_user_edit.html', context)


@login_required
@user_passes_test(is_superuser)
def admin_user_delete(request, user_id):
    """Delete a user"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Prevent deleting self
        if user.id == request.user.id:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('dashboard:admin_user_detail', user_id=user_id)
        
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('dashboard:admin_users_list')
    
    return redirect('dashboard:admin_users_list')


@login_required
@user_passes_test(is_superuser)
def admin_user_toggle_status(request, user_id):
    """Toggle user active status"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Prevent disabling self
        if user.id == request.user.id:
            messages.error(request, 'You cannot disable your own account.')
            return redirect('dashboard:admin_user_detail', user_id=user_id)
        
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} {status} successfully.')
        return redirect('dashboard:admin_user_detail', user_id=user_id)
    
    return redirect('dashboard:admin_users_list')
