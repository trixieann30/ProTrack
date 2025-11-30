from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('employee', 'Employee'),
        ('admin', 'Administrator'),
    )
    
    PROGRAM_CHOICES = (
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
        ('OTHER', 'Other'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    program = models.CharField(
        max_length=20, 
        choices=PROGRAM_CHOICES, 
        blank=True,
        help_text='For students: degree program. For employees: area of expertise'
    )
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')],
        blank=True
    )
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    profile_picture_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='URL to profile picture in Supabase storage'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"

    def get_profile_picture_url(self):
        """Get profile picture URL (Supabase URL or default avatar - never local files)"""
        # Only use Supabase URL
        if self.profile_picture_url:
            return self.profile_picture_url
        
        # Return default avatar (never use local files)
        name = self.get_full_name() or self.username
        return f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=667eea&color=fff"
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    skills = models.TextField(help_text="Comma-separated list of skills", blank=True)
    certifications = models.TextField(help_text="Comma-separated list of certifications", blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Create your models here.
