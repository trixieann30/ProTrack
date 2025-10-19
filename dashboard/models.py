from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


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
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TrainingCategory, on_delete=models.SET_NULL, null=True, related_name='courses')
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
