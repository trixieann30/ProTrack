from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class TrainingCategory(models.Model):
    """Categories for organizing training courses"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-book', help_text='FontAwesome icon class')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Training Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TrainingCourse(models.Model):
    """Training courses available in the system"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    )
    
    LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    
    PROGRAM_CHOICES = (
        ('ALL', 'All Programs'),
        ('BSIT', 'BS Information Technology'),
        ('BSCS', 'BS Computer Science'),
        ('BSARCH', 'BS Architecture'),
        ('BSCE', 'BS Civil Engineering'),
        ('BSME', 'BS Mechanical Engineering'),
        ('BSEE', 'BS Electrical Engineering'),
        ('BSBA', 'BS Business Administration'),
        ('BSED', 'BS Education'),
        ('BSHRM', 'BS Hotel & Restaurant Management'),
        ('BSTM', 'BS Tourism Management'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TrainingCategory, on_delete=models.SET_NULL, null=True, related_name='courses')
    target_programs = models.CharField(
        max_length=200,
        default='ALL',
        help_text='Comma-separated programs (e.g., "BSIT,BSCS") or "ALL" for all programs'
    )
    instructor = models.CharField(max_length=100)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.5)])
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    max_participants = models.PositiveIntegerField(default=30)
    prerequisites = models.TextField(blank=True, help_text='Required knowledge or courses')
    learning_outcomes = models.TextField(help_text='What participants will learn')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    thumbnail = models.ImageField(upload_to='training_thumbnails/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def enrolled_count(self):
        """Count of currently enrolled users"""
        return self.enrollments.filter(status__in=['enrolled', 'in_progress']).count()
    
    @property
    def is_full(self):
        """Check if course has reached max capacity"""
        return self.enrolled_count >= self.max_participants
    
    @property
    def completion_rate(self):
        """Calculate percentage of users who completed the course"""
        total = self.enrollments.count()
        if total == 0:
            return 0
        completed = self.enrollments.filter(status='completed').count()
        return round((completed / total) * 100, 1)


class TrainingSession(models.Model):
    """Scheduled sessions for training courses"""
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='sessions')
    session_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, help_text='Physical location or online meeting link')
    is_online = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_date', 'start_time']
    
    def __str__(self):
        return f"{self.course.title} - {self.session_name} ({self.start_date})"


class Enrollment(models.Model):
    """Track user enrollments in training courses"""
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='enrollments')
    session = models.ForeignKey(TrainingSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    enrolled_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    progress_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    feedback = models.TextField(blank=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_enrollments')
    notes = models.TextField(blank=True, help_text='Internal notes about this enrollment')
    completed_materials = models.ManyToManyField('TrainingMaterial', blank=True, related_name='completed_by_enrollments')
    
    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.status})"
    
    def mark_completed(self, score=None):
        """Mark enrollment as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completion_date = timezone.now().date()
        self.progress_percentage = 100
        if score is not None:
            self.score = score
        self.save()
    
    def cancel(self):
        """Cancel enrollment"""
        self.status = 'cancelled'
        self.save()


class TrainingMaterial(models.Model):
    """Training materials/resources for courses (US-07)"""
    MATERIAL_TYPE_CHOICES = (
        ('document', 'Document'),
        ('video', 'Video'),
        ('presentation', 'Presentation'),
        ('quiz', 'Quiz'),
        ('other', 'Other'),
    )
    
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES, default='document')
    file_url = models.URLField(max_length=500, help_text='URL to file in Supabase storage')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes', null=True, default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_materials')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_required = models.BooleanField(default=False, help_text='Is this material required for course completion?')
    order = models.PositiveIntegerField(default=0, help_text='Display order')
    
    class Meta:
        ordering = ['course', 'order', '-uploaded_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Certificate(models.Model):
    """Training certificates for completed courses (US-09)"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('revoked', 'Revoked'),
    )
    
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True, help_text='Leave blank for no expiry')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    certificate_url = models.URLField(max_length=500, blank=True, help_text='URL to certificate PDF in Supabase storage')
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='issued_certificates')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Certificate {self.certificate_number} - {self.enrollment.user.username}"

class Quiz(models.Model):
    material = models.OneToOneField(TrainingMaterial, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    pass_mark = models.PositiveIntegerField(default=50, validators=[MaxValueValidator(100)])

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_in_the_blanks', 'Fill in the Blanks'),
        ('identification', 'Identification'),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    correct_answer = models.CharField(max_length=255, blank=True, null=True)  # For Identification, Fill in the Blanks
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.text

class Choice(models.Model):
    # ... (rest of the code remains the same)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuizAttempt(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.enrollment.user.username}'s attempt on {self.quiz.title}"

class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True)

    def __str__(self):
        return f"Answer to {self.question.text}"


class TaskDeadline(models.Model):
    """User-defined deadlines for training materials."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_deadlines')
    material = models.ForeignKey(TrainingMaterial, on_delete=models.CASCADE, related_name='deadlines')
    due_date = models.DateField()

    class Meta:
        unique_together = ('user', 'material')

    def __str__(self):
        return f"{self.user.username}'s deadline for {self.material.title}"
# Add this to your existing dashboard/models.py file

class Notification(models.Model):
    """User notifications for various events"""
    NOTIFICATION_TYPES = (
        ('enrollment', 'Training Enrollment'),
        ('completion', 'Course Completion'),
        ('certificate', 'Certificate Issued'),
        ('assignment', 'Training Assigned'),
        ('reminder', 'Reminder'),
        ('announcement', 'Announcement'),
        ('system', 'System Notification'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, help_text='URL to navigate when clicked')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: reference to related objects
    related_enrollment = models.ForeignKey(
        'Enrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )    
    related_certificate = models.ForeignKey(
        'Certificate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'

    )   
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
        
    def mark_as_unread(self):
        self.is_read = False
        self.save() 

    def is_unread(self):
        return not self.is_read

    def get_notification_type_display(self):
        return dict(self.NOTIFICATION_TYPES)[self.notification_type]

    def get_related_object(self):
        if self.related_enrollment:
            return self.related_enrollment
        elif self.related_certificate:
            return self.related_certificate
        else:
            return None

    def get_related_object_type(self):
        if self.related_enrollment:
            return 'enrollment'
        elif self.related_certificate:
            return 'certificate'
        else:
            return None

    def get_related_object_url(self):
        related_object = self.get_related_object()
        if related_object:
            return related_object.get_absolute_url()
        else:
            return None
    
    def get_related_object_title(self):
        related_object = self.get_related_object()
        if related_object:
            return related_object.title
        else:
            return None

    def get_related_object_user(self):
        related_object = self.get_related_object()
        if related_object:
            return related_object.user
        else:
            return None

    def get_related_object_user_name(self):
        related_object_user = self.get_related_object_user()
        if related_object_user:
            return related_object_user.username
        else:
            return None

    def get_related_object_user_email(self):
        related_object_user = self.get_related_object_user()
        if related_object_user:
            return related_object_user.email
        else:
            return None
    
    def get_related_object_user_full_name(self):
        related_object_user = self.get_related_object_user()
        if related_object_user:
            return related_object_user.get_full_name()
        else:
            return None

    def get_related_object_user_profile_picture(self):
        related_object_user = self.get_related_object_user()
        if related_object_user:
            return related_object_user.profile_picture
        else:
            return None

    def get_related_object_user_profile_picture_url(self):
        related_object_user_profile_picture = self.get_related_object_user_profile_picture()
        if related_object_user_profile_picture:
            return related_object_user_profile_picture.url
        else:
            return None

    @classmethod
    def create_enrollment_notification(cls, enrollment, assigned_by=None):
        """Create notification when user enrolls or is assigned to a course."""
        user = enrollment.user
        course = enrollment.course
        
        # Get user's notification preferences
        prefs = getattr(user, 'notification_preferences', None)
        if not prefs:
            from accounts.models import NotificationPreference
            prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        
        # Debug logging
        print("=" * 70)
        print(f"🔔 CREATING ENROLLMENT NOTIFICATION FOR: {user.username}")
        print("=" * 70)
        
        # Determine notification type and message
        if assigned_by is not None:
            notification_type = 'assignment'
            assigned_name = assigned_by.get_full_name() or assigned_by.username
            title = 'New Training Assigned'
            message = f'{assigned_name} assigned you to "{course.title}".'
            
            # Check email preference for assignment
            send_email = prefs.email_on_assignment
            create_notification = prefs.notify_on_assignment
            
            print(f"📋 Type: ASSIGNMENT (by {assigned_name})")
            print(f"📧 Email toggle: {send_email}")
            print(f"🔔 In-app toggle: {create_notification}")
        else:
            notification_type = 'enrollment'
            title = 'Enrollment Confirmed'
            message = f'You have been enrolled in "{course.title}".'
            
            # Check email preference for enrollment
            send_email = prefs.email_on_enrollment
            create_notification = prefs.notify_on_enrollment
            
            print(f"📋 Type: ENROLLMENT (self-enrolled)")
            print(f"📧 Email toggle: {send_email}")
            print(f"🔔 In-app toggle: {create_notification}")
        
        link = reverse('dashboard:course_detail', args=[course.id])
        
        # Create in-app notification if enabled
        notification = None
        if create_notification:
            notification = cls.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                link=link,
                related_enrollment=enrollment,
            )
            print(f"✅ In-app notification CREATED (ID: {notification.id})")
        else:
            print(f"❌ In-app notification SKIPPED (toggle is OFF)")
        
        # Send email if enabled
        if send_email:
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                send_mail(
                    subject=f'ProTrack: {title}',
                    message=f'{message}\n\nView details: {settings.SITE_URL}{link}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                print(f"✅ Email SENT to {user.email}")
            except Exception as e:
                print(f"❌ Email FAILED: {e}")
        else:
            print(f"❌ Email SKIPPED (toggle is OFF)")
        
        print("=" * 70)
        print()
        
        return notification
    @classmethod
    def create_completion_notification(cls, enrollment):
        """Create notification when course is completed."""
        user = enrollment.user
        course = enrollment.course
        
        # Get preferences
        prefs = getattr(user, 'notification_preferences', None)
        if not prefs:
            from accounts.models import NotificationPreference
            prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        
        title = 'Course Completed'
        message = f'Great job! You completed "{course.title}".'
        link = reverse('dashboard:my_training')
        
        # Create in-app notification if enabled
        notification = None
        if prefs.notify_on_completion:
            notification = cls.objects.create(
                user=user,
                notification_type='completion',
                title=title,
                message=message,
                link=link,
                related_enrollment=enrollment,
            )
        
        # Send email if enabled
        if prefs.email_on_completion:
            try:
                send_mail(
                    subject=f'ProTrack: {title}',
                    message=f'{message}\n\nView your training: {settings.SITE_URL}{link}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")
        
        return notification
    
    @classmethod
    def create_certificate_notification(cls, certificate):
        """Create notification when certificate is issued."""
        enrollment = certificate.enrollment
        user = enrollment.user
        course = enrollment.course
        
        # Get preferences
        prefs = getattr(user, 'notification_preferences', None)
        if not prefs:
            from accounts.models import NotificationPreference
            prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        
        title = 'Certificate Issued'
        message = f'A certificate has been issued for "{course.title}".'
        link = certificate.certificate_url or reverse('dashboard:certifications')
        
        # Create in-app notification if enabled
        notification = None
        if prefs.notify_on_certificate:
            notification = cls.objects.create(
                user=user,
                notification_type='certificate',
                title=title,
                message=message,
                link=link,
                related_certificate=certificate,
            )
        
        # Send email if enabled
        if prefs.email_on_certificate:
            try:
                send_mail(
                    subject=f'ProTrack: {title}',
                    message=f'{message}\n\nDownload: {settings.SITE_URL}{link}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")
        
        return notification