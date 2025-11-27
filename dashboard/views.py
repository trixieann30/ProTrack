import json
from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import CustomUser
from training.models import TrainingModule

from .models import (
    Certificate,
    Enrollment,
    Notification,
    TaskDeadline,
    TrainingCategory,
    TrainingCourse,
    TrainingMaterial,
    Quiz,
    Question,
    Choice,
    TrainingSession,
)


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
    
    # Get user's enrollments
    enrollments = Enrollment.objects.filter(user=user).select_related('course', 'session')
    
    # Active enrollments (in progress)
    active_enrollments = enrollments.filter(status__in=['enrolled', 'in_progress']).order_by('-enrolled_date')[:5]
    
    # Completed enrollments
    completed_enrollments = enrollments.filter(status='completed')
    
    # Statistics
    total_enrollments = enrollments.count()
    in_progress_count = enrollments.filter(status='in_progress').count()
    completed_count = completed_enrollments.count()
    
    # Calculate completion rate
    completion_rate = round((completed_count / total_enrollments * 100), 1) if total_enrollments > 0 else 0
    
    # Total hours completed
    total_hours = completed_enrollments.aggregate(
        total=Sum('course__duration_hours')
    )['total'] or 0
    
    # Average score
    avg_score = completed_enrollments.filter(
        score__isnull=False
    ).aggregate(Avg('score'))['score__avg']
    avg_score = round(avg_score, 1) if avg_score else 0
    
    # Recent certificates
    recent_certificates = Certificate.objects.filter(
        enrollment__user=user,
        status='issued'
    ).select_related('enrollment__course').order_by('-issue_date')[:3]
    
    # Upcoming sessions (for enrolled courses)
    upcoming_sessions = TrainingSession.objects.filter(
        enrollments__user=user,
        start_date__gte=timezone.now().date()
    ).select_related('course').order_by('start_date')[:5]
    
    # Quick actions checklist
    quick_actions = []
    
    # Check if user has incomplete profile
    if not user.first_name or not user.last_name:
        quick_actions.append({
            'title': 'Complete Your Profile',
            'description': 'Add your personal information',
            'icon': 'fa-user-edit',
            'url': 'accounts:edit_profile',
            'priority': 'high'
        })
    
    # Check if user has active enrollments
    if in_progress_count > 0:
        quick_actions.append({
            'title': 'Continue Learning',
            'description': f'{in_progress_count} course(s) in progress',
            'icon': 'fa-book-reader',
            'url': 'dashboard:my_training',
            'priority': 'medium'
        })
    
    # Check if user has no enrollments
    if total_enrollments == 0:
        quick_actions.append({
            'title': 'Browse Training Catalog',
            'description': 'Discover available courses',
            'icon': 'fa-graduation-cap',
            'url': 'dashboard:training_catalog',
            'priority': 'high'
        })
    
    # Check for certificates to claim
    pending_certificates = Certificate.objects.filter(
        enrollment__user=user,
        status='pending'
    ).count()
    
    if pending_certificates > 0:
        quick_actions.append({
            'title': 'Certificates Pending',
            'description': f'{pending_certificates} certificate(s) ready',
            'icon': 'fa-certificate',
            'url': 'dashboard:certifications',
            'priority': 'medium'
        })
    
    context = {
        'user': user,
        'active_enrollments': active_enrollments,
        'total_enrollments': total_enrollments,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'completion_rate': completion_rate,
        'total_hours': total_hours,
        'avg_score': avg_score,
        'recent_certificates': recent_certificates,
        'upcoming_sessions': upcoming_sessions,
        'quick_actions': quick_actions,
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
@user_passes_test(is_superuser)
def archived_courses(request, course_id):
    if request.method == 'POST' and request.user.is_superuser:
        course = get_object_or_404(TrainingModule, id=course_id)
        course.status = 'archived'
        course.save()
    return redirect('dashboard:training_catalog')  # Redirect back to catalog

@login_required
@user_passes_test(is_superuser)
def archive_training(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    # Only archived courses
    courses = TrainingModule.objects.filter(status='archived')

    if search_query:
        courses = courses.filter(title__icontains=search_query)

    if category_filter:
        courses = courses.filter(category__icontains=category_filter)

    categories = TrainingCategory.objects.all()

    context = {
        'courses': courses,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
    }
    return render(request, 'dashboard/archive_training.html', context)

@login_required
@user_passes_test(is_superuser)
def restore_course(request, course_id):
    if request.method == 'POST':
        # Get the course safely from TrainingCourse
        course = get_object_or_404(TrainingCourse, id=course_id)
        course.status = 'active'  # Change status back to active
        course.save()
        messages.success(request, f'Course "{course.title}" has been restored.')
    return redirect('dashboard:training_catalog')

@login_required
@user_passes_test(is_superuser)
def create_training(request):
    """Admin view to create a new training course"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructor = request.POST.get('instructor')
        duration_hours = request.POST.get('duration_hours')
        level = request.POST.get('level')
        category_id = request.POST.get('category')
        status = request.POST.get('status', 'active')
        
        # Get category safely
        category = TrainingCategory.objects.filter(id=category_id).first() if category_id else None
        
        # Create TrainingCourse
        course = TrainingModule.objects.create(
            title=title,
            description=description,
            instructor=instructor,
            duration_hours=duration_hours,
            level=level,
            category=category,
            status=status
        )
        
        messages.success(request, f'Training "{title}" created successfully.')
        return redirect('dashboard:training_catalog')
    
    # GET request → show form
    categories = TrainingCategory.objects.all()
    level_choices = TrainingCourse.LEVEL_CHOICES  # if you have LEVEL_CHOICES in model
    context = {
        'categories': categories,
        'level_choices': level_choices,
    }
    return render(request, 'dashboard/create_training.html', context)

@login_required
@user_passes_test(is_superuser)
def archive_course(request, course_id):
    """Archive a training course (set status to 'archived')"""
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    if request.method == 'POST':
        course.status = 'archived'
        course.save()
        messages.success(request, f'Course "{course.title}" has been archived.')
        return redirect('dashboard:training_catalog')
    
    # Optional: show confirmation page
    context = {'course': course}
    return render(request, 'dashboard/archive_course_confirm.html', context)

@login_required
@user_passes_test(is_superuser)
def archive_training(request):
    """Admin view to list all courses and allow archiving (optional page)."""
    courses = TrainingCourse.objects.filter(status='archived')
    
    context = {
        'courses': courses,
    }
    return render(request, 'dashboard/archive_training.html', context)

@login_required
def certifications(request):
    """Display user's certificates (US-09)"""
    user = request.user
    
    # Get user's certificates through their completed enrollments
    if user.is_superuser:
        # Admins see all certificates
        certificates = Certificate.objects.select_related(
            'enrollment__user',
            'enrollment__course',
            'issued_by'
        ).order_by('-issue_date')
    else:
        # Regular users see only their own certificates
        certificates = Certificate.objects.filter(
            enrollment__user=user
        ).select_related(
            'enrollment__course',
            'issued_by'
        ).order_by('-issue_date')
    
    context = {
        'certificates': certificates,
        'user': user,
    }
    
    return render(request, 'dashboard/certifications.html', context)


# ============ TRAINING VIEWS ============

@login_required
def training_catalog(request):
    """Display all available training courses"""
    courses = TrainingCourse.objects.filter(status='active')
    categories = TrainingCategory.objects.all()
    
    # Filter by user's program (for students and employees)
    if not request.user.is_superuser and request.user.program:
        # Show courses for user's program OR courses for ALL programs
        courses = courses.filter(
            Q(target_programs='ALL') | 
            Q(target_programs__icontains=request.user.program)
        )
    
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

    # Get user's enrollments to show status on catalog page
    user_enrollments = []
    if request.user.is_authenticated:
        user_enrollments = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    
    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': category_id,
        'selected_level': level,
        'search_query': search_query,
        'user_enrollments': user_enrollments,
    }
    return render(request, 'dashboard/training_catalog.html', context)


@login_required
def course_detail(request, course_id):
    """Display detailed information about a specific course"""
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    # Check if user is already enrolled
    is_enrolled = Enrollment.objects.filter(
        user=request.user,
        course=course,
        status__in=['pending', 'enrolled', 'in_progress']
    ).exists()
    
    # Get enrollment if exists
    enrollment = None
    if is_enrolled:
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status__in=['pending', 'enrolled', 'in_progress']
        ).first()
    
    # Calculate enrollment percentage (THIS IS NEW)
    if course.max_participants > 0:
        enrollment_percentage = round((course.enrolled_count / course.max_participants) * 100, 1)
    else:
        enrollment_percentage = 0
    
    # Get upcoming sessions
    upcoming_sessions = course.sessions.filter(
        start_date__gte=timezone.now().date()
    ).order_by('start_date')[:5]
    
    # Get recent enrollments (for admin)
    recent_enrollments = None
    if request.user.is_superuser:
        recent_enrollments = course.enrollments.select_related('user').order_by('-enrolled_date')[:10]

    # Get training materials for the course
    materials = course.materials.all().select_related('quiz').order_by('order')
    completed_materials_ids = []
    if enrollment:
        completed_materials_ids = list(enrollment.completed_materials.values_list('id', flat=True))
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'enrollment_percentage': enrollment_percentage,  
        'upcoming_sessions': upcoming_sessions,
        'recent_enrollments': recent_enrollments,
        'materials': materials,
        'completed_materials_ids': completed_materials_ids,
    }
    return render(request, 'dashboard/course_detail.html', context)

@login_required
def enroll_course(request, course_id):
    """Enroll user in a training course"""
    if request.method == 'POST':
        if request.user.is_superuser:
            messages.error(request, 'Administrators cannot enroll in courses.')
            return redirect('dashboard:course_detail', course_id=course_id)

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
        
        enrollment = Enrollment.objects.create(
            user=request.user,
            course=course,
            session=session,
            status='enrolled'
        )
        
        # CREATE NOTIFICATION - THIS IS NEW
        Notification.create_enrollment_notification(enrollment)
        
        messages.success(request, f'Successfully enrolled in {course.title}!')
        return redirect('dashboard:my_training')
    
    return redirect('dashboard:training_catalog')


@login_required
def my_training(request):
    """Display user's enrolled training courses"""
    
    # Get all enrollments
    all_enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related('course', 'session').order_by('-enrolled_date')
    
    # Separate by status
    active_enrollments = all_enrollments.filter(
        status__in=['enrolled', 'in_progress']
    )
    
    completed_enrollments = all_enrollments.filter(
        status='completed'
    )
    
    pending_enrollments = all_enrollments.filter(
        status='pending'
    )
    
    # Calculate statistics
    total_enrollments = all_enrollments.count()
    in_progress_count = active_enrollments.count()
    completed_count = completed_enrollments.count()
    
    # Calculate total hours (completed courses)
    total_hours = completed_enrollments.aggregate(
        total=Sum('course__duration_hours')
    )['total'] or 0
    
    # Calculate average score
    avg_score = completed_enrollments.filter(
        score__isnull=False
    ).aggregate(Avg('score'))['score__avg']
    avg_score = round(avg_score, 1) if avg_score else 0
    
    context = {
        'enrollments': all_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'pending_enrollments': pending_enrollments,
        'total_enrollments': total_enrollments,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'total_hours': total_hours,
        'avg_score': avg_score,
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

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().prefetch_related('choices')

    if request.method == 'POST':
        score = 0
        total_questions = questions.count()

        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')
            if user_answer:
                if question.question_type == 'multiple_choice':
                    selected_choice = get_object_or_404(Choice, id=user_answer)
                    if selected_choice.is_correct:
                        score += 1
                else:
                    if user_answer.strip().lower() == question.correct_answer.strip().lower():
                        score += 1

        percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0

        # Save the quiz attempt
        QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=percentage_score
        )

        messages.success(request, f'You have completed the quiz. Your score is {percentage_score:.2f}%.')
        return redirect('dashboard:course_detail', course_id=quiz.material.course.id)  # Corrected syntax error here

    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'dashboard/take_quiz.html', context)

@login_required
@user_passes_test(is_superuser)
def manage_quiz(request, material_id):
    """Admin view to manage a quiz's questions and choices."""
    material = get_object_or_404(TrainingMaterial, id=material_id, material_type='quiz')
    quiz, created = Quiz.objects.get_or_create(
        material=material,
        defaults={'title': material.title, 'description': material.description}
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_pass_mark':
            pass_mark = request.POST.get('pass_mark')
            if pass_mark is not None:
                quiz.pass_mark = int(pass_mark)
                quiz.save()
                messages.success(request, 'Pass mark updated successfully.')

        elif action == 'edit_question':
            question_id = request.POST.get('question_id')
            question = get_object_or_404(Question, id=question_id)
            question.text = request.POST.get('text')
            if question.question_type != 'multiple_choice':
                question.correct_answer = request.POST.get('correct_answer')
            question.save()
            messages.success(request, 'Question updated successfully.')

        elif action == 'add_choice':
            question_id = request.POST.get('question_id')
            question = get_object_or_404(Question, id=question_id)
            text = request.POST.get('text')
            is_correct = request.POST.get('is_correct') == 'true'
            Choice.objects.create(question=question, text=text, is_correct=is_correct)
            messages.success(request, 'Choice added successfully.')

        else:  # Default action is to add a new question
            text = request.POST.get('text')
            question_type = request.POST.get('question_type')
            Question.objects.create(quiz=quiz, text=text, question_type=question_type)
            messages.success(request, 'Question added successfully.')
            
        return redirect('dashboard:manage_quiz', material_id=material.id)

    questions = quiz.questions.all().prefetch_related('choices')

    context = {
        'material': material,
        'questions': questions,
    }
    return render(request, 'dashboard/manage_quiz.html', context)


@login_required
@user_passes_test(is_superuser)
def edit_course(request, course_id):
    """Admin view to edit an existing training course."""
    course = get_object_or_404(TrainingCourse, id=course_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructor = request.POST.get('instructor')
        duration_hours = request.POST.get('duration_hours')
        level = request.POST.get('level')
        category_id = request.POST.get('category')
        status = request.POST.get('status', 'active')

        category = TrainingCategory.objects.filter(id=category_id).first() if category_id else None

        course.title = title
        course.description = description
        course.instructor = instructor
        course.duration_hours = duration_hours
        course.level = level
        course.category = category
        course.status = status
        course.save()

        messages.success(request, f'Course "{title}" updated successfully.')
        return redirect('dashboard:course_detail', course_id=course.id)

    categories = TrainingCategory.objects.all()
    level_choices = TrainingCourse.LEVEL_CHOICES
    context = {
        'course': course,
        'categories': categories,
        'level_choices': level_choices,
    }
    return render(request, 'dashboard/edit_course.html', context)

@user_passes_test(is_superuser)
def assign_training(request):
    """Admin view to add a new task (TrainingMaterial) to a course."""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        material_type = request.POST.get('material_type')
        order = request.POST.get('order', 0)

        try:
            course = get_object_or_404(TrainingCourse, id=course_id)

            # Create the new training material
            new_material = TrainingMaterial.objects.create(
                course=course,
                title=title,
                description=description,
                material_type=material_type,
                order=order
            )

            # Notify enrolled users and update their progress
            enrollments = Enrollment.objects.filter(course=course, status__in=['enrolled', 'in_progress'])
            for enrollment in enrollments:
                # Create a notification for the user
                Notification.objects.create(
                    user=enrollment.user,
                    notification_type='new_material',
                    title=f'New Task Added to {course.title}',
                    message=f'A new task, "{title}", has been added to the course you are enrolled in.',
                    link=reverse('dashboard:course_detail', args=[course.id])
                )

                # Recalculate progress percentage
                total_materials = course.materials.count()
                if total_materials > 0:
                    completed_count = enrollment.completed_materials.count()
                    progress = round((completed_count / total_materials) * 100)
                    enrollment.progress_percentage = progress
                    enrollment.save()

            messages.success(request, f'Successfully added task "{title}" to {course.title} and notified {enrollments.count()} users.')
            return redirect('dashboard:course_detail', course_id=course.id)

        except Exception as e:
            messages.error(request, f'Error adding task: {str(e)}')
            return redirect('dashboard:assign_training')

    # GET request - show the form
    courses = TrainingCourse.objects.filter(status='active')
    context = {
        'courses': courses,
    }
    return render(request, 'dashboard/assign_training.html', context)

@login_required
@user_passes_test(is_superuser)
def create_training(request):
    """Admin view to create a new training course"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructor = request.POST.get('instructor')
        duration_hours = request.POST.get('duration_hours')
        level = request.POST.get('level')
        category_id = request.POST.get('category')
        status = request.POST.get('status', 'active')

        # Get category safely
        category = TrainingCategory.objects.filter(id=category_id).first() if category_id else None

        # Create the course
        TrainingModule.objects.create(
            title=title,
            description=description,
            instructor=instructor,
            duration_hours=duration_hours,
            level=level,
            category=category,
            status=status
        )
        messages.success(request, f'Training "{title}" created successfully.')
        return redirect('dashboard:training_catalog')

    # GET request → show form
    categories = TrainingCategory.objects.all()
    level_choices = TrainingCourse.LEVEL_CHOICES
    context = {
        'categories': categories,
        'level_choices': level_choices,
    }
    return render(request, 'dashboard/create_training.html', context)

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
        'selected_user': user,
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
        'selected_user': user,
    }
    return render(request, 'dashboard/admin_user_edit.html', context)


@login_required
@user_passes_test(is_superuser)
def admin_user_delete(request, user_id):
    """Delete a user"""
    user_to_delete = get_object_or_404(CustomUser, id=user_id)
    
    # Prevent deleting yourself
    if user_to_delete.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('dashboard:admin_user_detail', user_id=user_id)
    
    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('dashboard:admin_users_list')
    
    # GET request → show confirmation template
    context = {'selected_user': user_to_delete}
    return render(request, 'dashboard/admin_user_delete.html', context)


@login_required
@require_POST
def mark_material_complete(request, enrollment_id, material_id):
    """Mark a training material as complete for an enrollment."""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
    material = get_object_or_404(TrainingMaterial, id=material_id, course=enrollment.course)

    # Add material to completed set
    enrollment.completed_materials.add(material)

    # Recalculate progress
    total_materials = enrollment.course.materials.count()
    if total_materials > 0:
        completed_count = enrollment.completed_materials.count()
        progress = round((completed_count / total_materials) * 100)
        enrollment.progress_percentage = progress
    
    # Check for course completion
    if enrollment.progress_percentage == 100 and enrollment.status != 'completed':
        enrollment.mark_completed()
        
        # Generate certificate
        certificate, created = Certificate.objects.get_or_create(
            enrollment=enrollment,
            defaults={
                'certificate_number': f'CERT-{enrollment.id}-{timezone.now().year}',
                'issue_date': timezone.now().date(),
                'status': 'draft',  # Set initial status to draft for admin approval
                'issued_by': request.user
            }
        )
        
        if created:
            messages.success(request, f"Congratulations! You have completed {enrollment.course.title} and earned a certificate.")
        else:
            messages.info(request, f"You have completed {enrollment.course.title}. Your certificate is available.")
    else:
        messages.success(request, f'Successfully marked "{material.title}" as complete.')
    
    enrollment.save()
    
    return redirect('dashboard:course_detail', course_id=enrollment.course.id)


@login_required
@user_passes_test(is_superuser)
def approve_certificate(request, certificate_id):
    """Admin view to approve a certificate and set an expiry date."""
    if request.method == 'POST':
        certificate = get_object_or_404(Certificate, id=certificate_id)
        expiry_date = request.POST.get('expiry_date')
        
        certificate.status = 'issued'
        if expiry_date:
            certificate.expiry_date = expiry_date
        
        certificate.save()
        messages.success(request, 'Certificate approved successfully.')
        return redirect('dashboard:certifications')
    
    return redirect('dashboard:certifications')


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


# ============ REPORTS VIEWS (US-03) ============

@login_required
@user_passes_test(is_superuser)
def reports(request):
    """Admin reports and analytics dashboard (US-03)"""
    
    # Overall Statistics
    total_courses = TrainingCourse.objects.count()
    active_courses = TrainingCourse.objects.filter(status='active').count()
    archived_courses = TrainingCourse.objects.filter(status='archived').count()
    
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(
        status__in=['enrolled', 'in_progress']
    ).count()
    completed_enrollments = Enrollment.objects.filter(status='completed').count()
    
    total_users = CustomUser.objects.filter(is_superuser=False).count()
    total_certificates = Certificate.objects.filter(status='issued').count()
    
    # Completion Rate
    if total_enrollments > 0:
        overall_completion_rate = round((completed_enrollments / total_enrollments) * 100, 1)
    else:
        overall_completion_rate = 0
    
    # Average Score
    avg_score = Enrollment.objects.filter(
        score__isnull=False
    ).aggregate(Avg('score'))['score__avg']
    avg_score = round(avg_score, 1) if avg_score else 0
    
    # Course Performance
    course_stats = TrainingCourse.objects.annotate(
        total_enrolled=Count('enrollments'),
        completed=Count('enrollments', filter=Q(enrollments__status='completed')),
        avg_score=Avg('enrollments__score', filter=Q(enrollments__score__isnull=False))
    ).filter(total_enrolled__gt=0).order_by('-total_enrolled')[:10]
    
    # Recent Enrollments
    recent_enrollments = Enrollment.objects.select_related(
        'user', 'course'
    ).order_by('-enrolled_date')[:10]
    
    # Recent Completions
    recent_completions = Enrollment.objects.filter(
        status='completed'
    ).select_related('user', 'course').order_by('-completion_date')[:10]
    
    # User Progress Summary
    user_progress = CustomUser.objects.filter(
        is_superuser=False
    ).annotate(
        total_enrollments=Count('enrollments'),
        completed_courses=Count('enrollments', filter=Q(enrollments__status='completed')),
        in_progress=Count('enrollments', filter=Q(enrollments__status='in_progress')),
        avg_score=Avg('enrollments__score', filter=Q(enrollments__score__isnull=False))
    ).filter(total_enrollments__gt=0).order_by('-completed_courses')[:10]
    
    # Monthly Enrollment Trend (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    
    # Get enrollments and group by month in Python (SQLite compatible)
    enrollments_recent = Enrollment.objects.filter(
        enrolled_date__gte=six_months_ago
    ).values('enrolled_date')
    
    monthly_data = defaultdict(int)
    for enrollment in enrollments_recent:
        if enrollment['enrolled_date']:
            month_key = enrollment['enrolled_date'].strftime('%Y-%m')
            monthly_data[month_key] += 1
    
    monthly_enrollments = [
        {'month': month, 'count': count}
        for month, count in sorted(monthly_data.items())
    ]
    
    # Category Performance
    category_stats = TrainingCategory.objects.annotate(
        course_count=Count('courses'),
        enrollment_count=Count('courses__enrollments'),
        completion_count=Count('courses__enrollments', filter=Q(courses__enrollments__status='completed'))
    ).filter(course_count__gt=0)
    
    # Certificates Issued (group by month in Python)
    certs_recent = Certificate.objects.filter(
        status='issued',
        issue_date__gte=six_months_ago
    ).values('issue_date')
    
    cert_monthly_data = defaultdict(int)
    for cert in certs_recent:
        if cert['issue_date']:
            month_key = cert['issue_date'].strftime('%Y-%m')
            cert_monthly_data[month_key] += 1
    
    certificates_by_month = [
        {'month': month, 'count': count}
        for month, count in sorted(cert_monthly_data.items())
    ]
    
    context = {
        # Overall Stats
        'total_courses': total_courses,
        'active_courses': active_courses,
        'archived_courses': archived_courses,
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'total_users': total_users,
        'total_certificates': total_certificates,
        'overall_completion_rate': overall_completion_rate,
        'avg_score': avg_score,
        
        # Detailed Stats
        'course_stats': course_stats,
        'recent_enrollments': recent_enrollments,
        'recent_completions': recent_completions,
        'user_progress': user_progress,
        'monthly_enrollments': monthly_enrollments,
        'category_stats': category_stats,
        'certificates_by_month': certificates_by_month,
    }
    
    return render(request, 'dashboard/reports.html', context)
@login_required
def notifications_list(request):
    """Display all notifications for the user"""
    notifications = Notification.objects.filter(user=request.user)[:50]
    
    # Mark as read if requested
    mark_read = request.GET.get('mark_read')
    if mark_read == 'all':
        notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()
    }
    return render(request, 'dashboard/notifications.html', context)

@login_required
def notifications_api(request):
    """API endpoint to get notifications as JSON"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:20]
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'type': n.notification_type,
                'title': n.title,
                'message': n.message,
                'link': n.link,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': get_time_ago(n.created_at),
            }
            for n in notifications
        ],
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()
    }
    return JsonResponse(data)

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)

@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read for the current user"""
    count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True, 'marked_count': count})

@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a notification"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)

def get_time_ago(datetime_obj):
    """Helper function to get human-readable time ago"""
    now = timezone.now()
    diff = now - datetime_obj
    
    if diff < timedelta(minutes=1):
        return 'Just now'
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif diff < timedelta(days=7):
        days = diff.days
        return f'{days} day{"s" if days != 1 else ""} ago'
    else:
        return datetime_obj.strftime('%b %d, %Y')
    
    return datetime_obj 

    return datetime_obj

def create_course_completion_notification(enrollment):
    """Call this when a course is marked as completed"""
    Notification.create_completion_notification(enrollment)

def create_certificate_issued_notification(certificate):
    """Call this when a certificate is issued"""
    Notification.create_certificate_notification(certificate)

# ============ CALENDAR VIEWS (US-01A) ============

from datetime import datetime
from django.urls import reverse
from django.http import JsonResponse


@login_required
def calendar(request):
    """Render the calendar page."""
    return render(request, 'dashboard/calendar.html')

@login_required
def get_calendar_events(request):
    """API endpoint to fetch calendar events for FullCalendar."""
    events = []
    if request.user.is_superuser:
        # Superusers see all training sessions
        sessions = TrainingSession.objects.all().select_related('course')
        for session in sessions:
            events.append({
                'title': f"{session.course.title} - {session.session_name}",
                'start': f"{session.start_date}T{session.start_time}",
                'end': f"{session.end_date}T{session.end_time}",
                'url': reverse('dashboard:course_detail', args=[session.course.id]),
                'color': '#3b82f6', # Blue for sessions
                'extendedProps': {
                    'location': session.location,
                    'is_online': session.is_online
                }
            })
    else:
        # Regular users see their course start and finish dates
        enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
        for enrollment in enrollments:
            # Default completion date to one day after start if not set
            end_date = enrollment.completion_date
            if not end_date:
                end_date = enrollment.enrolled_date + timedelta(days=1)

            events.append({
                'id': enrollment.id,
                'title': enrollment.course.title,
                'start': enrollment.enrolled_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'allDay': True,
                'color': '#3b82f6' if enrollment.completion_date else '#60a5fa', # Darker blue for set, lighter for unset
                'url': reverse('dashboard:course_detail', args=[enrollment.course.id]),
                # Make the event editable, but only from the end
                'editable': True,
                'eventStartEditable': False,
                'eventDurationEditable': True, 
            })

    return JsonResponse(events, safe=False)

@login_required
@require_POST
def update_enrollment_completion(request):
    """API endpoint to update the completion date of an enrollment."""
    try:
        data = json.loads(request.body)
        enrollment_id = data.get('id')
        completion_date_str = data.get('completion_date')

        if not all([enrollment_id, completion_date_str]):
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
        enrollment.completion_date = datetime.strptime(completion_date_str, '%Y-%m-%d').date()
        enrollment.save()

        return JsonResponse({'success': True})

    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid data format'}, status=400)
    except Enrollment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Enrollment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)