from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import CustomUser, UserProfile
from dashboard.models import Notification
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
from dashboard.supabase_utils import upload_profile_picture
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import base64
import logging

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # ✨ NEW: Create welcome notification for new user
            try:
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title='Welcome to ProTrack!',
                    message=f'Hello {user.get_full_name() or user.username}! Welcome to ProTrack - your skills and training management platform. Get started by browsing our training catalog and enrolling in courses that match your interests.',
                    link='/dashboard/training/catalog/',
                    is_read=False
                )
            except Exception as e:
                # Log error but don't fail registration
                print(f"⚠️ Could not create welcome notification: {e}")
            
            # Auto-login: Authenticate and login the user
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                messages.success(request, f'Welcome {username}! Your account has been created successfully.')
                
                # Redirect based on user type
                if user.is_superuser:
                    return redirect('dashboard:admin_dashboard')
                else:
                    return redirect('dashboard:user_dashboard')
            else:
                messages.error(request, 'Account created but login failed. Please login manually.')
                return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        # Redirect based on user role
        if self.request.user.is_superuser:
            return '/dashboard/admin/'
        else:
            return '/dashboard/user/'
    
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'Welcome back, {username}!')
        return super().form_valid(form)

custom_login = CustomLoginView.as_view()

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Parse comma-separated skills and certifications into lists
    skills_list = [skill.strip() for skill in profile.skills.split(',') if skill.strip()] if profile.skills else []
    certifications_list = [cert.strip() for cert in profile.certifications.split(',') if cert.strip()] if profile.certifications else []
    
    context = {
        'profile': profile,
        'skills_list': skills_list,
        'certifications_list': certifications_list,
    }
    
    return render(request, 'accounts/profile.html', context)


logger = logging.getLogger(__name__)

@login_required
def edit_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            # 1. HANDLE CROPPED PROFILE PICTURE (base64 from frontend)
            cropped_data = request.POST.get('cropped_image_data')
            if cropped_data:
                try:
                    format, imgstr = cropped_data.split(';base64,')  # "data:image/png;base64,..."
                    ext = format.split('/')[-1]  # png, jpeg, etc.
                    data = ContentFile(base64.b64decode(imgstr), name=f"profile_{user.id}.{ext}")

                    # Upload to Supabase
                    success, url, error = upload_profile_picture(user.id, data)

                    if success:
                        user.profile_picture_url = url
                        user.save()
                        messages.success(request, "Profile picture updated!")
                    else:
                        messages.error(request, f"Upload failed: {error}")
                        return redirect('accounts:edit_profile')

                except Exception as e:
                    messages.error(request, f"Error processing image: {str(e)}")
                    return redirect('accounts:edit_profile')

            # 2. SAVE CUSTOMUSER FIELDS
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.phone_number = form.cleaned_data['phone_number']
            user.department = form.cleaned_data['department']
            user.position = form.cleaned_data['position']
            user.date_of_birth = form.cleaned_data['date_of_birth']
            user.save()

            # 3. SAVE USERPROFILE FIELDS
            form.save()

            messages.success(request, "Your profile has been updated!")
            return redirect('accounts:edit_profile')

    else:
        # Pre-populate CustomUser values
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'department': user.department,
            'position': user.position,
            'date_of_birth': user.date_of_birth,
        }
        form = UserProfileForm(initial=initial_data, instance=profile)

    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def send_verification_email(request):
    """Send email verification link to user"""
    user = request.user
    
    # Check if already verified
    if user.email_verified:
        messages.info(request, 'Your email is already verified!')
        return redirect('accounts:profile')
    
    # Check if email backend is configured
    from django.conf import settings
    if not hasattr(settings, 'SENDGRID_API_KEY') or not settings.SENDGRID_API_KEY:
        messages.error(request, 'Email service not configured. Please contact administrator.')
        logger.error('SendGrid API key not configured')
        return redirect('accounts:profile')
    
    try:
        # Generate verification token
        token = get_random_string(64)
        user.email_verification_token = token
        user.save()
        
        # Build verification URL
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'token': token})
        )
        
        # Email content
        subject = 'Verify Your Email - ProTrack'
        message = f"""Hello {user.get_full_name() or user.username},

Thank you for registering with ProTrack!

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The ProTrack Team
"""
        
        logger.info(f'📧 Sending verification email to {user.email}')
        
        # Send email
        from django.core.mail import send_mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f'✅ Email sent successfully to {user.email}')
        messages.success(request, f'Verification email sent to {user.email}. Check your inbox!')
        
    except Exception as e:
        logger.error(f'❌ Email failed: {str(e)}', exc_info=True)
        messages.error(request, f'Failed to send email: {str(e)[:100]}')
    
    return redirect('accounts:profile')

@login_required
def verify_email(request, token):
    """Verify user's email with token"""
    user = request.user
    
    if user.email_verification_token == token:
        user.email_verified = True
        user.email_verification_token = ''  # Clear the token
        user.save()
        messages.success(request, 'Your email has been verified successfully!')
    else:
        messages.error(request, 'Invalid or expired verification link.')
    
    return redirect('accounts:profile')

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

@login_required
def custom_logout(request):
    """Logout the user and redirect to home page"""
    logout(request)
    return redirect('home')
