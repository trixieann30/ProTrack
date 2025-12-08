import json
from collections import defaultdict
from datetime import datetime, timedelta
import mimetypes
import logging
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
from accounts.models import NotificationPreference
from accounts.forms import NotificationPreferenceForm
import os

logger = logging.getLogger(__name__)
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
    QuizAttempt,
    Answer,
    TrainingSession,
)

from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from .supabase_utils import upload_training_material, delete_training_material
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
import uuid
from django.http import HttpResponse

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
    
    # Get user's enrollments with fresh data
    enrollments = Enrollment.objects.filter(user=user).select_related('course', 'session')
    
    # Active enrollments (in progress) - exclude cancelled
    active_enrollments = enrollments.filter(
        status__in=['enrolled', 'in_progress']
    ).order_by('-enrolled_date')[:5]
    
    # Completed enrollments
    completed_enrollments = enrollments.filter(status='completed')
    
    # Statistics - REAL-TIME CALCULATION
    total_enrollments = enrollments.exclude(status='cancelled').count()  # Exclude cancelled
    in_progress_count = enrollments.filter(status='in_progress').count()
    completed_count = completed_enrollments.count()
    
    # Calculate completion rate
    completion_rate = 0
    if total_enrollments > 0:
        completion_rate = round((completed_count / total_enrollments * 100), 1)
    
    # Total hours completed
    total_hours = completed_enrollments.aggregate(
        total=Sum('course__duration_hours')
    )['total'] or 0
    
    # Average score
    avg_score_result = completed_enrollments.filter(
        score__isnull=False
    ).aggregate(Avg('score'))
    avg_score = round(avg_score_result['score__avg'], 1) if avg_score_result['score__avg'] else 0
    
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
    
    # Check for certificates to claim (draft = pending approval)
    pending_certificates = Certificate.objects.filter(
        enrollment__user=user,
        status='draft'
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
        course = TrainingCourse.objects.create(
            title=title,
            description=description,
            instructor=instructor,
            duration_hours=duration_hours,
            level=level,
            category=category,
            status=status
        )
        
        # Notify users about new course
        try:
            recipients = CustomUser.objects.filter(is_active=True, is_superuser=False)
            if course.target_programs and course.target_programs != 'ALL':
                programs = [p.strip() for p in course.target_programs.split(',') if p.strip()]
                if programs:
                    recipients = recipients.filter(program__in=programs)

            notified = 0
            for u in recipients:
                pref = NotificationPreference.objects.filter(user=u).first()
                if pref and not getattr(pref, 'notify_on_announcement', True):
                    continue
                Notification.objects.create(
                    user=u,
                    notification_type='announcement',
                    title=f'New Course: {course.title}',
                    message=f'A new course "{course.title}" is now available. Check it out!',
                    link=reverse('dashboard:course_detail', args=[course.id])
                )
                notified += 1
        except Exception as e:
            try:
                logger.warning(f"Failed to send new course notifications: {e}")
            except Exception:
                pass

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
    logger.info(f"certifications view called: user={user.id}, is_superuser={user.is_superuser}")

    if user.is_superuser:
        logger.info("Loading admin certifications view")
        # Admins see all certificates
        certificates = Certificate.objects.select_related(
            'enrollment__user',
            'enrollment__course',
            'issued_by'
        ).order_by('-issue_date')

        # Count pending certificates for admin notification
        pending_count = certificates.filter(status='draft').count()
        logger.info(f"Admin view: total certificates={certificates.count()}, pending={pending_count}")

    else:
        logger.info("Loading user certifications view")
        # Regular users see their issued certificates and any pending (draft) certificates
        certificates = Certificate.objects.filter(
            enrollment__user=user,
            status__in=['issued', 'draft']
        ).select_related(
            'enrollment__course',
            'issued_by'
        ).order_by('-issue_date')

        # Count user's pending (draft) certificates for UI badges
        pending_count = certificates.filter(status='draft').count()
        logger.info(f"User view: total certificates={certificates.count()}, pending={pending_count}")

    context = {
        'certificates': certificates,
        'user': user,
        'pending_count': pending_count,  # NEW: For admin notification
    }

    logger.info(f"Rendering certifications template with {len(certificates)} certificates")
    return render(request, 'dashboard/certifications.html', context)



# ============ TRAINING VIEWS ============

@login_required
def training_catalog(request):
    courses = TrainingCourse.objects.filter(status='active')
    categories = TrainingCategory.objects.all()
    
    if not request.user.is_superuser and request.user.program:
        courses = courses.filter(
            Q(target_programs='ALL') | Q(target_programs__icontains=request.user.program)
        )

    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)

    level = request.GET.get('level')
    if level:
        courses = courses.filter(level=level)

    search_query = request.GET.get('search')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instructor__icontains=search_query)
        )

    # Get user's active enrollments
    user_enrollments = []
    if request.user.is_authenticated:
        user_enrollments = Enrollment.objects.filter(
            user=request.user,
            status__in=['pending', 'enrolled', 'in_progress']
        ).values_list('course_id', flat=True)

    # Get user's completed courses
    user_completed_courses = []
    if request.user.is_authenticated:
        user_completed_courses = Enrollment.objects.filter(
            user=request.user,
            status='completed'
        ).values_list('course_id', flat=True)

    context = {
        'courses': courses,
        'categories': categories,
        'user_enrollments': user_enrollments,
        'user_completed_courses': user_completed_courses,  # <-- add this
        'search_query': search_query,
        'category_filter': category_id,
        'level_filter': level,
        'course_levels': TrainingCourse.LEVEL_CHOICES,
        'total_courses': courses.count(),
    }
    return render(request, 'dashboard/training_catalog.html', context)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    # Get enrollment if exists (including completed)
    enrollment = Enrollment.objects.filter(
        user=request.user,
        course=course,
    ).first()  # Grab the first enrollment regardless of status
    
    # Check if user is enrolled or completed
    is_enrolled = enrollment is not None and enrollment.status != 'completed'
    has_completed = enrollment is not None and enrollment.status == 'completed'
    
    # Enrollment percentage
    if course.max_participants > 0:
        enrollment_percentage = round((course.enrolled_count / course.max_participants) * 100, 1)
    else:
        enrollment_percentage = 0
    
    # Upcoming sessions
    upcoming_sessions = course.sessions.filter(
        start_date__gte=timezone.now().date()
    ).order_by('start_date')[:5]
    
    # Recent enrollments (for admin)
    recent_enrollments = None
    if request.user.is_superuser:
        recent_enrollments = course.enrollments.select_related('user').order_by('-enrolled_date')[:10]

    # Materials
    materials = course.materials.all().select_related('quiz').order_by('order')
    completed_materials_ids = []
    if enrollment:
        completed_materials_ids = list(enrollment.completed_materials.values_list('id', flat=True))
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'is_enrolled': is_enrolled,          # for "Already Enrolled"
        'has_completed': has_completed,      # for "Course Completed"
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
        
        # ✅ FIX: Check if user has completed this course (has certificate)
        completed_enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status='completed'
        ).first()
        
        if completed_enrollment:
            # Check if certificate exists
            has_certificate = Certificate.objects.filter(
                enrollment=completed_enrollment,
                status__in=['draft', 'issued']
            ).exists()
            
            if has_certificate:
                messages.warning(
                    request, 
                    'You have already completed this course and have a certificate. You cannot re-enroll.'
                )
                return redirect('dashboard:my_training')
        
        # Check if already enrolled (only active enrollments)
        existing_enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status__in=['enrolled', 'in_progress', 'pending']
        ).first()
        
        if existing_enrollment:
            messages.warning(request, 'You are already enrolled in this course.')
            return redirect('dashboard:my_training')
        
        # Check for cancelled enrollment and reactivate or create new
        cancelled_enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status='cancelled'
        ).first()
        
        if cancelled_enrollment:
            # Reactivate cancelled enrollment
            cancelled_enrollment.status = 'enrolled'
            cancelled_enrollment.enrolled_date = timezone.now()
            cancelled_enrollment.start_date = None
            cancelled_enrollment.completion_date = None
            cancelled_enrollment.progress_percentage = 0
            cancelled_enrollment.score = None
            if session_id:
                cancelled_enrollment.session = TrainingSession.objects.filter(id=session_id).first()
            cancelled_enrollment.save()
            enrollment = cancelled_enrollment
            messages.success(request, f'Successfully re-enrolled in {course.title}!')
        else:
            # Create new enrollment
            session = None
            if session_id:
                session = TrainingSession.objects.filter(id=session_id).first()
            
            enrollment = Enrollment.objects.create(
                user=request.user,
                course=course,
                session=session,
                status='enrolled'
            )
            messages.success(request, f'Successfully enrolled in {course.title}!')
        
        # CREATE NOTIFICATION
        Notification.create_enrollment_notification(enrollment)
        
        return redirect('dashboard:my_training')
    
    return redirect('dashboard:training_catalog')

@login_required
def my_training(request):
    """Display user's enrolled training courses"""

    all_enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related('course', 'session').order_by('-enrolled_date')

    active_enrollments = all_enrollments.filter(status__in=['enrolled', 'in_progress'])
    completed_enrollments = all_enrollments.filter(status='completed')
    pending_enrollments = all_enrollments.filter(status='pending')

    # ----------------------------------------------------
    # 🔥 FIX: Calculate completion rate for each enrollment
    # ----------------------------------------------------
    for enrollment in all_enrollments:
        course = enrollment.course

        total_items = course.materials.filter(is_required=True).count()
        completed_items = enrollment.completed_materials.filter(is_required=True).count()

        if total_items > 0:
            enrollment.completion_rate = round((completed_items / total_items) * 100)
        else:
            enrollment.completion_rate = 0
    # ----------------------------------------------------

    total_enrollments = all_enrollments.count()
    in_progress_count = active_enrollments.count()
    completed_count = completed_enrollments.count()

    total_hours = completed_enrollments.aggregate(
        total=Sum('course__duration_hours')
    )['total'] or 0

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
    """Take a quiz and calculate score"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().prefetch_related('choices')
    
    # Get user's enrollment for this course
    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=quiz.material.course,
        status__in=['enrolled', 'in_progress']
    )
    
    if request.method == 'POST':
        score = 0
        total_questions = questions.count()
        
        if total_questions == 0:
            messages.error(request, 'This quiz has no questions.')
            return redirect('dashboard:course_detail', course_id=quiz.material.course.id)
        
        # Create quiz attempt
        quiz_attempt = QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz,
            score=0  # Will update after calculation
        )
        
        # Grade each question
        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')
            if not user_answer:
                continue  # Skip unanswered questions
            
            is_correct = False
            
            if question.question_type == 'multiple_choice':
                try:
                    selected_choice = Choice.objects.get(id=user_answer)
                    if selected_choice.is_correct:
                        score += 1
                        is_correct = True
                    # Save answer
                    Answer.objects.create(
                        attempt=quiz_attempt,
                        question=question,
                        choice=selected_choice
                    )
                except Choice.DoesNotExist:
                    pass
                    
            elif question.question_type == 'true_false':
                if user_answer.strip().lower() == question.correct_answer.strip().lower():
                    score += 1
                    is_correct = True
                # Save answer
                Answer.objects.create(
                    attempt=quiz_attempt,
                    question=question,
                    text_answer=user_answer
                )
                
            elif question.question_type in ['fill_in_the_blanks', 'identification']:
                # Case-insensitive comparison, strip whitespace
                if user_answer.strip().lower() == question.correct_answer.strip().lower():
                    score += 1
                    is_correct = True
                # Save answer
                Answer.objects.create(
                    attempt=quiz_attempt,
                    question=question,
                    text_answer=user_answer
                )
        
        # Calculate percentage
        percentage_score = round((score / total_questions) * 100, 2) if total_questions > 0 else 0
        
        # Update quiz attempt
        quiz_attempt.score = percentage_score
        quiz_attempt.save()
        
        # Update enrollment score
        enrollment.score = percentage_score
        
        # Check if passed
        passed = percentage_score >= quiz.pass_mark
        
        if passed:
            messages.success(
                request,
                f'Congratulations! You passed with {percentage_score}% (Pass mark: {quiz.pass_mark}%). Score: {score}/{total_questions}'
            )
            
            # FIX: Mark quiz material as complete
            enrollment.completed_materials.add(quiz.material)
            
            # Update progress
            total_materials = enrollment.course.materials.count()
            if total_materials > 0:
                completed_count = enrollment.completed_materials.count()
                progress = round((completed_count / total_materials) * 100)
                enrollment.progress_percentage = progress
                
                # FIX: Check for course completion
                if progress == 100:
                    enrollment.status = 'completed'
                    enrollment.completion_date = timezone.now().date()
                    
                    # Create draft certificate
                    certificate, created = Certificate.objects.get_or_create(
                        enrollment=enrollment,
                        defaults={
                            'certificate_number': f'CERT-{enrollment.id}-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}',
                            'issue_date': timezone.now().date(),
                            'status': 'draft',  # Admin must approve
                        }
                    )
                    
                    if created:
                        # Notify user
                        Notification.objects.create(
                            user=enrollment.user,
                            notification_type='completion',
                            title='🎉 Course Completed!',
                            message=f'Congratulations! You completed "{enrollment.course.title}". Your certificate is pending approval.',
                            link=reverse('dashboard:certifications')
                        )
                        
                        # Notify admins
                        admins = CustomUser.objects.filter(is_superuser=True)
                        for admin in admins:
                            Notification.objects.create(
                                user=admin,
                                notification_type='system',
                                title='Certificate Pending Approval',
                                message=f'{enrollment.user.get_full_name() or enrollment.user.username} completed "{enrollment.course.title}"',
                                link=reverse('dashboard:certifications')
                            )
                        
                        messages.success(request, '🎓 Course completed! Your certificate is pending approval.')
                
                enrollment.save()
        else:
            messages.warning(
                request,
                f'You scored {percentage_score}% (Pass mark: {quiz.pass_mark}%). Score: {score}/{total_questions}. Please try again to improve your score.'
            )
        
        return redirect('dashboard:course_detail', course_id=quiz.material.course.id)
    
    # GET request - show quiz
    context = {
        'quiz': quiz,
        'questions': questions,
        'enrollment': enrollment,
    }
    
    return render(request, 'dashboard/take_quiz.html', context)
@login_required
@user_passes_test(is_superuser)
def manage_quiz(request, material_id):
    """Admin view to manage a quiz's questions and choices."""
    logger.info(f"manage_quiz called: user={request.user.id}, material_id={material_id}")

    try:
        material = get_object_or_404(TrainingMaterial, id=material_id, material_type='quiz')
        logger.info(f"Found material: {material.title}, type={material.material_type}")

        quiz, created = Quiz.objects.get_or_create(
            material=material,
            defaults={'title': material.title, 'description': material.description}
        )
        logger.info(f"Quiz {'created' if created else 'found'}: {quiz.title}")

        if request.method == 'POST':
            action = request.POST.get('action')
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            logger.info(f"POST request: action={action}, is_ajax={is_ajax}")

            if action == 'update_pass_mark':
                pass_mark = request.POST.get('pass_mark')
                logger.info(f"Updating pass mark to: {pass_mark}")
                if pass_mark is not None:
                    quiz.pass_mark = int(pass_mark)
                    quiz.save()
                    if is_ajax:
                        return JsonResponse({'success': True, 'pass_mark': quiz.pass_mark, 'message': 'Pass mark updated successfully.'})
                    messages.success(request, 'Pass mark updated successfully.')

            elif action == 'edit_question':
                question_id = request.POST.get('question_id')
                logger.info(f"Editing question: {question_id}")
                question = get_object_or_404(Question, id=question_id)
                question.text = request.POST.get('text')
                if question.question_type != 'multiple_choice':
                    question.correct_answer = request.POST.get('correct_answer')
                question.save()
                if is_ajax:
                    # Return updated fields so the client can update the UI
                    return JsonResponse({'success': True, 'question_id': question.id, 'text': question.text, 'correct_answer': question.correct_answer if question.question_type != 'multiple_choice' else None})
                messages.success(request, 'Question updated successfully.')

            elif action == 'add_choice':
                question_id = request.POST.get('question_id')
                logger.info(f"Adding choice to question: {question_id}")
                question = get_object_or_404(Question, id=question_id)
                text = request.POST.get('text')
                is_correct = request.POST.get('is_correct') == 'true'
                choice = Choice.objects.create(question=question, text=text, is_correct=is_correct)
                if is_ajax:
                    # Return choice details so client can add it to the list
                    return JsonResponse({
                        'success': True,
                        'choice_id': choice.id,
                        'text': choice.text,
                        'is_correct': choice.is_correct,
                        'message': 'Choice added successfully.'
                    })
                messages.success(request, 'Choice added successfully.')

            elif action == 'save_all':
                logger.info("Bulk saving all questions")
                # Bulk update multiple questions at once
                # Expect POST keys like question_<id>_text and question_<id>_correct
                for key, value in request.POST.items():
                    if not key.startswith('question_'):
                        continue
                    # key format: question_<id>_field
                    parts = key.split('_')
                    if len(parts) < 3:
                        continue
                    try:
                        qid = int(parts[1])
                    except ValueError:
                        continue
                    field = '_'.join(parts[2:])
                    try:
                        question = Question.objects.get(id=qid, quiz=quiz)
                    except Question.DoesNotExist:
                        continue

                    if field == 'text':
                        question.text = value
                    elif field == 'correct':
                        # non-multiple choice correct answer
                        question.correct_answer = value

                    question.save()

                messages.success(request, 'All questions saved successfully.')
                # After bulk save, redirect back to the course page for the material
                try:
                    if is_ajax:
                        return JsonResponse({'success': True, 'redirect': reverse('dashboard:course_detail', args=[material.course.id])})
                    return redirect('dashboard:course_detail', course_id=material.course.id)
                except Exception:
                    # Fallback to manage page if course lookup fails
                    if is_ajax:
                        return JsonResponse({'success': True, 'redirect': reverse('dashboard:manage_quiz', args=[material.id])})
                    return redirect('dashboard:manage_quiz', material_id=material.id)

            else:  # Default action is to add a new question
                text = request.POST.get('text')
                question_type = request.POST.get('question_type')
                logger.info(f"Adding new question: type={question_type}")
                Question.objects.create(quiz=quiz, text=text, question_type=question_type)
                messages.success(request, 'Question added successfully.')

            return redirect('dashboard:manage_quiz', material_id=material.id)

        questions = quiz.questions.all().prefetch_related('choices')
        logger.info(f"Rendering template with {questions.count()} questions")

        context = {
            'material': material,
            'questions': questions,
        }
        return render(request, 'dashboard/manage_quiz.html', context)

    except Exception as e:
        logger.error(f"Error in manage_quiz: {str(e)}", exc_info=True)
        raise


@login_required
@user_passes_test(is_superuser)
def edit_course(request, course_id):
    """Admin view to edit an existing training course."""
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    if request.method == 'POST':
        # Handle text fields
        course.title = request.POST.get('title')
        course.description = request.POST.get('description')
        course.instructor = request.POST.get('instructor')
        course.duration_hours = request.POST.get('duration_hours')
        course.level = request.POST.get('level')
        course.status = request.POST.get('status', 'active')
        
        # Handle category
        category_id = request.POST.get('category')
        if category_id:
            course.category = TrainingCategory.objects.filter(id=category_id).first()
        
        # Handle thumbnail upload
        if 'thumbnail' in request.FILES:
            uploaded_file = request.FILES['thumbnail']
            
            # Validate file type
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_ext not in allowed_extensions:
                messages.error(request, f'Invalid file type. Allowed: {", ".join(allowed_extensions)}')
                return redirect('dashboard:edit_course', course_id=course.id)
            
            # Upload to Supabase
            try:
                from .supabase_utils import SupabaseStorage
                storage = SupabaseStorage(use_service_key=True)
                
                # Create file path
                import time
                timestamp = int(time.time())
                file_path = f"course_thumbnails/course_{course.id}_{timestamp}{file_ext}"
                
                # Upload file
                success, url, error = storage.upload_file(uploaded_file, 'Uploadfiles', file_path, upsert=True)
                
                if success:
                    course.thumbnail = url
                    messages.success(request, 'Course thumbnail updated successfully!')
                else:
                    messages.error(request, f'Failed to upload thumbnail: {error}')
            except Exception as e:
                messages.error(request, f'Error uploading thumbnail: {str(e)}')
        
        course.save()
        messages.success(request, f'Course "{course.title}" updated successfully.')
        return redirect('dashboard:course_detail', course_id=course.id)
    
    # GET request
    categories = TrainingCategory.objects.all()
    level_choices = TrainingCourse.LEVEL_CHOICES
    
    context = {
        'course': course,
        'categories': categories,
        'level_choices': level_choices,
    }
    return render(request, 'dashboard/edit_course.html', context)

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
        course = TrainingCourse.objects.create(
            title=title,
            description=description,
            instructor=instructor,
            duration_hours=duration_hours,
            level=level,
            category=category,
            status=status
        )
        # Notify users about new course
        try:
            recipients = CustomUser.objects.filter(is_active=True, is_superuser=False)
            if course.target_programs and course.target_programs != 'ALL':
                programs = [p.strip() for p in course.target_programs.split(',') if p.strip()]
                if programs:
                    recipients = recipients.filter(program__in=programs)

            notified = 0
            for u in recipients:
                pref = NotificationPreference.objects.filter(user=u).first()
                if pref and not getattr(pref, 'notify_on_announcement', True):
                    continue
                Notification.objects.create(
                    user=u,
                    notification_type='announcement',
                    title=f'New Course: {course.title}',
                    message=f'A new course "{course.title}" is now available. Check it out!',
                    link=reverse('dashboard:course_detail', args=[course.id])
                )
                notified += 1
        except Exception as e:
            try:
                logger.warning(f"Failed to send new course notifications: {e}")
            except Exception:
                pass

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
    # Clear any existing messages to prevent them from showing inappropriately
    # This helps with the issue where messages appear in settings from other pages
    storage = messages.get_messages(request)
    storage.used = True  # Mark all messages as used/consumed

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
    
    # Filters
    search_query = request.GET.get('search', '').strip()
    user_type = request.GET.get('user_type', '')
    status = request.GET.get('status', '')

    if user_type:
        if user_type == 'admin':
            users = users.filter(is_superuser=True)
        else:
            users = users.filter(user_type=user_type.lower())  # ensure lowercase match

    if status:
        users = users.filter(is_active=(status == 'active'))

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'user_type': user_type,
        'status': status,
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
            
            # FIXED: Generate certificate immediately with proper status
            certificate, created = Certificate.objects.get_or_create(
                enrollment=enrollment,
                defaults={
                    'certificate_number': f'CERT-{enrollment.id}-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}',
                    'issue_date': timezone.now().date(),
                    'status': 'draft',  # Start as draft, admin must approve
                }
            )
            
            if created:
                # Notify user about completion
                Notification.objects.create(
                    user=enrollment.user,
                    notification_type='completion',
                    title='Course Completed!',
                    message=f'Congratulations! You have completed "{enrollment.course.title}". Your certificate is pending approval.',
                    link=reverse('dashboard:certifications')
                )
                
                # Notify admins about pending certificate
                admins = CustomUser.objects.filter(is_superuser=True)
                for admin in admins:
                    Notification.objects.create(
                        user=admin,
                        notification_type='system',
                        title='Certificate Pending Approval',
                        message=f'{enrollment.user.get_full_name() or enrollment.user.username} completed "{enrollment.course.title}" and needs certificate approval.',
                        link=reverse('dashboard:certifications')
                    )
                
                messages.success(request, f"Congratulations! You have completed {enrollment.course.title}. Your certificate is pending approval.")
            else:
                messages.info(request, f"You have completed {enrollment.course.title}.")
        else:
            messages.success(request, f'Successfully marked "{material.title}" as complete.')
        
        enrollment.save()
    
    return redirect('dashboard:course_detail', course_id=enrollment.course.id)
@login_required
@user_passes_test(is_superuser)
def approve_certificate(request, certificate_id):
    """Admin view to approve a certificate and generate PDF."""
    if request.method == 'POST':
        certificate = get_object_or_404(Certificate, id=certificate_id)
        expiry_date_str = request.POST.get('expiry_date')
        
        try:
            # Set expiry date if provided
            if expiry_date_str:
                certificate.expiry_date = expiry_date_str
            
            # Generate PDF and upload to Supabase
            pdf_success, pdf_url = generate_and_upload_certificate(certificate)
            
            if pdf_success:
                # Update certificate status
                certificate.status = 'issued'
                certificate.certificate_url = pdf_url
                certificate.issued_by = request.user
                certificate.save()
                
                # Create notification for user
                Notification.create_certificate_notification(certificate)
                
                messages.success(
                    request,
                    f'Certificate approved and issued to {certificate.enrollment.user.username}'
                )
            else:
                messages.error(request, 'Failed to generate certificate PDF')
        
        except Exception as e:
            messages.error(request, f'Error approving certificate: {str(e)}')
            import traceback
            print(traceback.format_exc())
        
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
    """API endpoint to get notifications as JSON - respects user preferences"""
    
    # Get user preferences
    prefs = getattr(request.user, 'notification_preferences', None)
    if not prefs:
        from accounts.models import NotificationPreference
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
    
    # Start with all notifications for this user
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Filter based on preferences
    allowed_types = []
    
    if prefs.notify_on_enrollment:
        allowed_types.extend(['enrollment', 'assignment'])
    if prefs.notify_on_completion:
        allowed_types.append('completion')
    if prefs.notify_on_certificate:
        allowed_types.append('certificate')
    if prefs.notify_on_reminder:
        allowed_types.append('reminder')
    if prefs.notify_on_announcement:
        allowed_types.append('announcement')
    
    # Always show system notifications
    allowed_types.append('system')
    
    # Filter notifications by allowed types
    notifications = notifications.filter(notification_type__in=allowed_types)[:20]
    
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
            } for n in notifications
        ],
        'unread_count': Notification.objects.filter(
            user=request.user,
            is_read=False,
            notification_type__in=allowed_types  # Only count allowed types
        ).count()
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
      
@login_required
def notification_settings(request):
    """Manage notification preferences"""
    
    # Get or create notification preferences for user
    preferences, created = NotificationPreference.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        # CRITICAL FIX: Manually handle all boolean fields
        # Unchecked checkboxes don't appear in POST data
        boolean_fields = [
            'email_on_enrollment',
            'email_on_completion',
            'email_on_certificate',
            'email_on_assignment',
            'email_on_reminder',
            'notify_on_enrollment',
            'notify_on_completion',
            'notify_on_certificate',
            'notify_on_assignment',
            'notify_on_reminder',
            'notify_on_announcement',
        ]
        
        # Debug logging
        print("=" * 50)
        print("SAVING NOTIFICATION PREFERENCES")
        print("=" * 50)
        
        # Update each field based on POST data
        for field in boolean_fields:
            # If field is in POST, it's checked (True)
            # If field is NOT in POST, it's unchecked (False)
            new_value = field in request.POST
            old_value = getattr(preferences, field)
            
            # Debug output
            if old_value != new_value:
                print(f"🔄 {field}: {old_value} → {new_value}")
            
            setattr(preferences, field, new_value)
        
        # Save preferences
        preferences.save()
        
        # Verify save
        preferences.refresh_from_db()
        print(f"✅ Saved! notify_on_enrollment = {preferences.notify_on_enrollment}")
        print("=" * 50)
        
        messages.success(request, 'Notification preferences updated successfully.')
        return redirect('dashboard:notification_settings')
    
    # GET request - show form
    form = NotificationPreferenceForm(instance=preferences)
    
    context = {
        'form': form,
        'preferences': preferences,
    }
    
    return render(request, 'dashboard/notification_settings.html', context)

@login_required
def debug_notification_preferences(request):
        """Debug view to check notification preferences"""
        from accounts.models import NotificationPreference
        
        prefs, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        debug_info = {
            'User': request.user.username,
            'Preferences Created': created,
            '---EMAIL NOTIFICATIONS---': '',
            'email_on_enrollment': prefs.email_on_enrollment,
            'email_on_completion': prefs.email_on_completion,
            'email_on_certificate': prefs.email_on_certificate,
            'email_on_assignment': prefs.email_on_assignment,
            'email_on_reminder': prefs.email_on_reminder,
            '---IN-APP NOTIFICATIONS---': '',
            'notify_on_enrollment': prefs.notify_on_enrollment,
            'notify_on_completion': prefs.notify_on_completion,
            'notify_on_certificate': prefs.notify_on_certificate,
            'notify_on_assignment': prefs.notify_on_assignment,
            'notify_on_reminder': prefs.notify_on_reminder,
            'notify_on_announcement': prefs.notify_on_announcement,
            '---DIGEST---': '',
            'daily_digest': prefs.daily_digest,
            'weekly_digest': prefs.weekly_digest,
        }
        
        return JsonResponse(debug_info, json_dumps_params={'indent': 2})
        # File Upload View
@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def upload_material(request, course_id):
    """
    Upload training material to Supabase storage
    Admin only - US-05
    """
    try:
        course = get_object_or_404(TrainingCourse, id=course_id)
        
        material_type = request.POST.get('material_type', 'document')
        
        # QUIZ FIX: Quizzes don't need file uploads
        if material_type == 'quiz':
            # Create quiz material without file
            material = TrainingMaterial.objects.create(
                course=course,
                title=request.POST.get('title', 'New Quiz'),
                description=request.POST.get('description', ''),
                material_type='quiz',
                file_url='',  # No file for quizzes
                file_name='quiz.json',
                file_size=0,
                uploaded_by=request.user,
                is_required=True,  # All materials are required for course completion
                order=int(request.POST.get('order', 0))
            )
            
            # Create Quiz object
            Quiz.objects.create(
                material=material,
                title=material.title,
                description=material.description,
                pass_mark=50  # Default pass mark
            )
            
            messages.success(request, f'Quiz "{material.title}" created! Add questions in the Manage Quiz page.')
            # If this was an AJAX request, return JSON; otherwise redirect to the manage page
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'material_id': material.id,
                    'message': 'Quiz created successfully. Add questions now.',
                    'redirect': reverse('dashboard:manage_quiz', args=[material.id])
                })
            else:
                return redirect('dashboard:manage_quiz', material.id)
        
        # Regular file upload for non-quiz materials
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file provided'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Validate file size (50MB)
        MAX_SIZE = 50 * 1024 * 1024
        if uploaded_file.size > MAX_SIZE:
            return JsonResponse({
                'success': False,
                'error': f'File size exceeds 50MB limit (got {uploaded_file.size / (1024*1024):.1f}MB)'
            }, status=400)
        
        # Validate file type
        allowed_extensions = {
            'document': ['.pdf', '.doc', '.docx', '.txt'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.webm'],
            'presentation': ['.ppt', '.pptx'],
            'other': ['.zip', '.rar']
        }
        
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        valid_extensions = allowed_extensions.get(material_type, [])
        
        if valid_extensions and file_ext not in valid_extensions:
            logger.warning(f"Invalid file type uploaded: {file_ext} for material type {material_type}")
            return JsonResponse({
                'success': False,
                'error': f'Invalid file type for {material_type}. Allowed: {", ".join(valid_extensions)}'
            }, status=400)
        
        # Upload to Supabase
        success, file_url, error = upload_training_material(course_id, uploaded_file)
        
        if not success:
            return JsonResponse({
                'success': False,
                'error': error or 'Upload failed'
            }, status=500)
        
        # Create TrainingMaterial record
        material = TrainingMaterial.objects.create(
            course=course,
            title=request.POST.get('title', uploaded_file.name),
            description=request.POST.get('description', ''),
            material_type=material_type,
            file_url=file_url,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            uploaded_by=request.user,
            is_required=True,  # All materials are required for course completion
            order=int(request.POST.get('order', 0))
        )
        
        # Create notifications for enrolled users
        enrollments = Enrollment.objects.filter(
            course=course,
            status__in=['enrolled', 'in_progress']
        )
        
        for enrollment in enrollments:
            Notification.objects.create(
                user=enrollment.user,
                notification_type='announcement',
                title=f'New Material: {material.title}',
                message=f'New {material_type} material has been added to {course.title}',
                link=reverse('dashboard:course_detail', args=[course.id])
            )
        
        messages.success(request, f'Successfully uploaded {uploaded_file.name}')

        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({
                'success': True,
                'material_id': material.id,
                'file_url': file_url,
                'message': 'File uploaded successfully'
            })
        else:
            # For normal form submits, redirect back to the course detail page
            return redirect('dashboard:course_detail', course_id=course.id)
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_superuser)
def edit_material(request, material_id):
    """
    Admin view to edit an existing training material
    """
    material = get_object_or_404(TrainingMaterial, id=material_id)

    if request.method == 'POST':
        try:
            # Update basic fields
            material.title = request.POST.get('title', material.title)
            material.description = request.POST.get('description', material.description)
            material.order = int(request.POST.get('order', material.order))

            # Handle file replacement for non-quiz materials
            if material.material_type != 'quiz' and 'file' in request.FILES:
                uploaded_file = request.FILES['file']

                # Validate file size (50MB)
                MAX_SIZE = 50 * 1024 * 1024
                if uploaded_file.size > MAX_SIZE:
                    messages.error(request, f'File size exceeds 50MB limit (got {uploaded_file.size / (1024*1024):.1f}MB)')
                    return redirect('dashboard:edit_material', material_id=material.id)

                # Validate file type
                allowed_extensions = {
                    'document': ['.pdf', '.doc', '.docx', '.txt'],
                    'video': ['.mp4', '.avi', '.mov', '.wmv', '.webm'],
                    'presentation': ['.ppt', '.pptx'],
                    'other': ['.zip', '.rar']
                }

                file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                valid_extensions = allowed_extensions.get(material.material_type, [])

                if valid_extensions and file_ext not in valid_extensions:
                    messages.error(request, f'Invalid file type for {material.material_type}. Allowed: {", ".join(valid_extensions)}')
                    return redirect('dashboard:edit_material', material_id=material.id)

                # Delete old file from Supabase if it exists
                if material.file_url:
                    success, error = delete_training_material(material.file_url)
                    if not success:
                        logger.warning(f"Failed to delete old file from Supabase: {error}")

                # Upload new file to Supabase
                success, file_url, error = upload_training_material(material.course.id, uploaded_file)

                if not success:
                    messages.error(request, f'Failed to upload new file: {error}')
                    return redirect('dashboard:edit_material', material_id=material.id)

                # Update file information
                material.file_url = file_url
                material.file_name = uploaded_file.name
                material.file_size = uploaded_file.size

            material.save()
            messages.success(request, f'Material "{material.title}" updated successfully.')
            return redirect('dashboard:course_detail', course_id=material.course.id)

        except Exception as e:
            logger.error(f"Edit material error: {str(e)}", exc_info=True)
            messages.error(request, f'Error updating material: {str(e)}')
            return redirect('dashboard:edit_material', material_id=material.id)

    context = {
        'material': material,
        'course': material.course,
    }
    return render(request, 'dashboard/edit_material.html', context)


        # Delete Material View
@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def delete_material(request, material_id):
            """
            Delete training material from Supabase and database
            Admin only - US-05
            """
            try:
                material = get_object_or_404(TrainingMaterial, id=material_id)
                course_id = material.course.id

                # If this is a quiz material, attempt to delete the Quiz and related objects first
                if material.material_type == 'quiz':
                    try:
                        quiz_obj = getattr(material, 'quiz', None)
                        if quiz_obj:
                            # Deleting the Quiz will cascade to Questions, Choices and Attempts
                            quiz_obj.delete()
                    except Exception as e:
                        logger.warning(f"Failed to delete associated Quiz object: {e}")

                # Delete from Supabase only if a file URL is present
                if material.file_url:
                    success, error = delete_training_material(material.file_url)
                    if not success:
                        logger.warning(f"Failed to delete file from Supabase: {error}")

                # Delete the TrainingMaterial record
                material_title = material.title
                material.delete()

                messages.success(request, f'Deleted material: {material_title}')

                is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Material deleted successfully'
                    })
                else:
                    return redirect('dashboard:course_detail', course_id=course_id)
                
            except Exception as e:
                logger.error(f"Delete error: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)


        # Certificate Generation and Download
@login_required
def download_certificate(request, certificate_id):
    """
    Download certificate PDF
    """
    try:
        certificate = get_object_or_404(
            Certificate.objects.select_related('enrollment__user', 'enrollment__course'),
            id=certificate_id
        )
        
        # Check permissions
        if not (request.user.is_superuser or certificate.enrollment.user == request.user):
            raise PermissionDenied("You don't have permission to download this certificate")
        
        # Check certificate status
        if certificate.status != 'issued':
            messages.warning(request, 'Certificate is not yet issued')
            return redirect('dashboard:certifications')
        
        # If certificate URL exists, redirect to it
        if certificate.certificate_url:
            return redirect(certificate.certificate_url)
        
        # Generate certificate PDF if not exists
        pdf_success, pdf_url = generate_and_upload_certificate(certificate)
        
        if pdf_success:
            certificate.certificate_url = pdf_url
            certificate.save()
            return redirect(pdf_url)
        else:
            messages.error(request, 'Failed to generate certificate')
            return redirect('dashboard:certifications')
    
    except Certificate.DoesNotExist:
        raise Http404("Certificate not found")
    except Exception as e:
        print(f"Certificate download error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        messages.error(request, 'Failed to download certificate')
        return redirect('dashboard:certifications')
def generate_and_upload_certificate(certificate):
    """
    Generate certificate PDF and upload to Supabase
    Returns: (success: bool, url: str)
    """
    try:
        # Generate PDF
        pdf_buffer = generate_certificate_pdf(certificate)
        if not pdf_buffer:
            print("Failed to generate PDF buffer")
            return False, None
        
        # Upload to Supabase
        from .supabase_utils import upload_certificate
        
        # Convert BytesIO to file-like object with name
        pdf_buffer.name = f"certificate_{certificate.certificate_number}.pdf"
        pdf_buffer.seek(0)
        
        success, url, error = upload_certificate(
            certificate.enrollment.id,
            pdf_buffer
        )
        
        if success:
            print(f"✓ Certificate uploaded successfully: {url}")
            return True, url
        else:
            print(f"✗ Failed to upload certificate: {error}")
            return False, None
    
    except Exception as e:
        print(f"✗ Certificate generation error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, None

# IMPROVED: Better PDF certificate design
def generate_certificate_pdf(certificate):
    """
    Generate a professional certificate PDF using ReportLab
    Returns a BytesIO buffer containing the PDF
    """
    try:
        buffer = BytesIO()
        
        # Create PDF in landscape mode
        c = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # =====================================================
        # MODERN CERTIFICATE DESIGN
        # =====================================================
        
        # Draw outer border (gold)
        c.setStrokeColor(colors.HexColor('#C9A961'))
        c.setLineWidth(6)
        c.roundRect(0.4*inch, 0.4*inch, width-0.8*inch, height-0.8*inch, 15)
        
        # Draw inner border (blue)
        c.setStrokeColor(colors.HexColor('#667eea'))
        c.setLineWidth(3)
        c.roundRect(0.6*inch, 0.6*inch, width-1.2*inch, height-1.2*inch, 10)
        
        # =====================================================
        # TITLE SECTION
        # =====================================================
        
        # Main title "CERTIFICATE"
        c.setFont("Helvetica-Bold", 60)
        c.setFillColor(colors.HexColor('#667eea'))
        c.drawCentredString(width/2, height-2*inch, "CERTIFICATE")
        
        # Subtitle "OF COMPLETION"
        c.setFont("Helvetica", 24)
        c.setFillColor(colors.black)
        c.drawCentredString(width/2, height-2.5*inch, "OF COMPLETION")
        
        # Decorative line
        c.setStrokeColor(colors.HexColor('#764ba2'))
        c.setLineWidth(2)
        c.line(width/2 - 3.5*inch, height-2.8*inch, width/2 + 3.5*inch, height-2.8*inch)
        
        # =====================================================
        # RECIPIENT SECTION
        # =====================================================
        
        # "This is to certify that"
        c.setFont("Helvetica", 16)
        c.setFillColor(colors.black)
        c.drawCentredString(width/2, height-3.6*inch, "This is to certify that")
        
        # Recipient name (gold and bold)
        c.setFont("Helvetica-Bold", 40)
        c.setFillColor(colors.HexColor('#764ba2'))
        user_name = certificate.enrollment.user.get_full_name() or certificate.enrollment.user.username
        c.drawCentredString(width/2, height-4.3*inch, user_name)
        
        # =====================================================
        # COURSE SECTION
        # =====================================================
        
        # "has successfully completed the course"
        c.setFont("Helvetica", 15)
        c.setFillColor(colors.black)
        c.drawCentredString(width/2, height-5*inch, "has successfully completed the course")
        
        # Course title (blue and bold)
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(colors.HexColor('#667eea'))
        course_title = certificate.enrollment.course.title
        
        # Handle long course titles
        if len(course_title) > 50:
            words = course_title.split()
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            c.drawCentredString(width/2, height-5.6*inch, line1)
            c.drawCentredString(width/2, height-6*inch, line2)
            info_y_position = height-6.7*inch
        else:
            c.drawCentredString(width/2, height-5.6*inch, course_title)
            info_y_position = height-6.3*inch
        
        # Course details (duration and instructor)
        c.setFont("Helvetica", 13)
        c.setFillColor(colors.HexColor('#666666'))
        course_info = f"Duration: {certificate.enrollment.course.duration_hours} hours | Instructor: {certificate.enrollment.course.instructor}"
        c.drawCentredString(width/2, info_y_position, course_info)
        
        # =====================================================
        # SIGNATURE AND DATES SECTION
        # =====================================================
        
        # Signature line
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(width/2 - 2*inch, 2.5*inch, width/2 + 2*inch, 2.5*inch)
        
        
        
        # Issued by name (if available)
        if certificate.issued_by:
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(width/2, 1.95*inch, 
                certificate.issued_by.get_full_name() or certificate.issued_by.username)
        
        # Date issued (left side)
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        date_str = certificate.issue_date.strftime("%B %d, %Y")
        c.drawString(1.5*inch, 1.6*inch, f"Date Issued: {date_str}")
        
        # Certificate number (right side)
        c.drawRightString(width-1.5*inch, 1.6*inch, f"Certificate No: {certificate.certificate_number}")
        
        # =====================================================
        # FOOTER
        # =====================================================
        
        # System name
        c.setFont("Helvetica-Oblique", 11)
        c.setFillColor(colors.grey)
        c.drawCentredString(width/2, 1*inch, "ProTrack - Skills & Training Management System")
        
        # Verification text
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(width/2, 0.7*inch, 
            "This certificate verifies successful completion of the training program")
        
        # Save and return
        c.save()
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"PDF generation error: {str(e)}", exc_info=True)
        return None
        # Bulk download materials (optional)
@login_required
def download_all_materials(request, course_id):
            """
            Download all course materials as a ZIP file
            """
            try:
                course = get_object_or_404(TrainingCourse, id=course_id)
                
                # Check enrollment
                is_enrolled = Enrollment.objects.filter(
                    user=request.user,
                    course=course
                ).exists()
                
                if not (request.user.is_superuser or is_enrolled):
                    raise PermissionDenied("You must be enrolled in this course")
                
                materials = course.materials.all()
                
                if not materials:
                    messages.warning(request, 'No materials available for download')
                    return redirect('dashboard:course_detail', course_id=course_id)
                
                # Create ZIP file
                import zipfile
                from io import BytesIO
                import requests
                
                zip_buffer = BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for material in materials:
                        try:
                            # Download file from Supabase
                            response = requests.get(material.file_url, timeout=30)
                            if response.status_code == 200:
                                zip_file.writestr(material.file_name, response.content)
                        except Exception as e:
                            logger.error(f"Failed to add {material.file_name}: {str(e)}")
                
                zip_buffer.seek(0)
                
                response = FileResponse(
                    zip_buffer,
                    content_type='application/zip',
                    as_attachment=True,
                    filename=f'{course.title}_materials.zip'
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Bulk download error: {str(e)}", exc_info=True)
                messages.error(request, 'Failed to download materials')
                return redirect('dashboard:course_detail', course_id=course_id)
@login_required
def view_material(request, enrollment_id, material_id):
    """
    View a training material in-browser and mark as complete when viewed
    """
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
    material = get_object_or_404(TrainingMaterial, id=material_id, course=enrollment.course)
    
    # Check if already completed
    is_completed = material.id in enrollment.completed_materials.values_list('id', flat=True)
    
    # Get file type
    file_extension = os.path.splitext(material.file_name)[1].lower()
    
    # Determine if file is viewable
    viewable_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm', '.wmv']
    is_viewable = file_extension in viewable_extensions
    
    context = {
        'enrollment': enrollment,
        'material': material,
        'is_completed': is_completed,
        'is_viewable': is_viewable,
        'file_extension': file_extension,
    }
    
    return render(request, 'dashboard/view_material.html', context)


@login_required
@require_POST
def mark_material_viewed(request, enrollment_id, material_id):
    """
    API endpoint to mark material as viewed/complete
    Called via JavaScript when user has viewed the file
    """
    logger.info(f"mark_material_viewed called: user={request.user.id}, enrollment={enrollment_id}, material={material_id}")
    try:
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
        material = get_object_or_404(TrainingMaterial, id=material_id, course=enrollment.course)

        logger.info(f"Found enrollment and material: enrollment.user={enrollment.user.id}, material.title={material.title}")

        # Check if already completed
        completed_ids = list(enrollment.completed_materials.values_list('id', flat=True))
        logger.info(f"Completed materials before: {completed_ids}")

        if material.id in completed_ids:
            logger.info("Material already completed")
            return JsonResponse({'success': True, 'message': 'Already marked as complete'})

        # Mark as complete
        enrollment.completed_materials.add(material)
        logger.info(f"Added material {material.id} to completed materials")

        # Recalculate progress
        total_materials = enrollment.course.materials.count()
        logger.info(f"Total materials in course: {total_materials}")

        if total_materials > 0:
            completed_count = enrollment.completed_materials.count()
            progress = round((completed_count / total_materials) * 100)
            enrollment.progress_percentage = progress
            logger.info(f"Progress updated: {completed_count}/{total_materials} = {progress}%")

            # Check for course completion
            if progress == 100 and enrollment.status != 'completed':
                logger.info("Course completion detected, marking as completed")
                enrollment.mark_completed()

                # Generate draft certificate
                certificate, created = Certificate.objects.get_or_create(
                    enrollment=enrollment,
                    defaults={
                        'certificate_number': f'CERT-{enrollment.id}-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}',
                        'issue_date': timezone.now().date(),
                        'status': 'draft',
                    }
                )

                if created:
                    logger.info("Draft certificate created")
                    # Notify user about completion
                    Notification.objects.create(
                        user=enrollment.user,
                        notification_type='completion',
                        title='Course Completed!',
                        message=f'Congratulations! You have completed "{enrollment.course.title}". Your certificate is pending approval.',
                        link=reverse('dashboard:certifications')
                    )

                    # Notify admins
                    admins = CustomUser.objects.filter(is_superuser=True)
                    for admin in admins:
                        Notification.objects.create(
                            user=admin,
                            notification_type='system',
                            title='Certificate Pending Approval',
                            message=f'{enrollment.user.get_full_name() or enrollment.user.username} completed "{enrollment.course.title}" and needs certificate approval.',
                            link=reverse('dashboard:certifications')
                        )
                else:
                    logger.info("Certificate already exists")

            enrollment.save()
            logger.info("Enrollment saved successfully")

        response_data = {
            'success': True,
            'message': 'Material marked as complete',
            'progress': enrollment.progress_percentage
        }
        logger.info(f"Returning success response: {response_data}")
        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error in mark_material_viewed: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
@login_required
def edit_choice(request):
    """
    Update an existing choice's text and correctness.
    Expects POST: choice_id, text, is_correct (true/false)
    Returns JSON: { success: True, choice_id, text, is_correct }
    """
    choice_id = request.POST.get('choice_id')
    if not choice_id:
        return JsonResponse({'success': False, 'message': 'choice_id required'}, status=400)

    choice = get_object_or_404(Choice, pk=choice_id)

    text = request.POST.get('text', '').strip()
    is_correct = request.POST.get('is_correct', 'false').lower() in ('true', '1', 'on')

    if text == '':
        return JsonResponse({'success': False, 'message': 'Choice text cannot be empty'}, status=400)

    choice.text = text
    choice.is_correct = is_correct
    choice.save()

    return JsonResponse({'success': True, 'choice_id': choice.id, 'text': choice.text, 'is_correct': choice.is_correct})


@require_POST
@login_required
def delete_choice(request):
    """
    Delete a choice by id.
    Expects POST: choice_id
    Returns JSON: { success: True, choice_id }
    """
    choice_id = request.POST.get('choice_id')
    if not choice_id:
        return JsonResponse({'success': False, 'message': 'choice_id required'}, status=400)

    choice = get_object_or_404(Choice, pk=choice_id)

    # Optional permission check:
    # if choice.question.quiz.owner != request.user and not request.user.is_staff:
    #     return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    choice.delete()
    return JsonResponse({'success': True, 'choice_id': choice_id})


@require_POST
@login_required
def delete_question(request):
    """
    Delete a question by id.
    Expects POST: question_id
    Returns JSON: { success: True, question_id }
    """
    question_id = request.POST.get('question_id')
    if not question_id:
        return JsonResponse({'success': False, 'message': 'question_id required'}, status=400)

    question = get_object_or_404(Question, pk=question_id)

    # Optional permission check: ensure the current user can delete this question.
    # Uncomment & adjust fields to your model's relationships.
    # quiz = getattr(question, 'quiz', None)
    # if quiz and getattr(quiz, 'owner', None) and quiz.owner != request.user and not request.user.is_staff:
    #     return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    question.delete()
    return JsonResponse({'success': True, 'question_id': question_id})