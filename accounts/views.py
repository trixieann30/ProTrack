from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import CustomUser, UserProfile
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
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
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
@login_required
def edit_profile(request):
    # Get the instances for both models
    user_instance = request.user
    profile_instance, created = UserProfile.objects.get_or_create(user=user_instance)

    if request.method == 'POST':
        # CRITICAL: Pass BOTH request.POST (text data) and request.FILES (image data)
        # We pass the UserProfile instance because the form's Meta class points to it.
        form = UserProfileForm(request.POST, request.FILES, instance=profile_instance) 
        
        if form.is_valid():
            
            # --- 1. Manually extract and save CustomUser fields ---
            user_instance.first_name = form.cleaned_data['first_name']
            user_instance.last_name = form.cleaned_data['last_name']
            user_instance.phone_number = form.cleaned_data['phone_number']
            user_instance.department = form.cleaned_data['department']
            user_instance.position = form.cleaned_data['position']
            user_instance.date_of_birth = form.cleaned_data['date_of_birth']
            
            # Handle profile picture update 
            # If a new file was uploaded, form.cleaned_data['profile_picture'] will contain the File object
            # If the field was left blank, it will be None
            if form.cleaned_data['profile_picture']:
                user_instance.profile_picture = form.cleaned_data['profile_picture']
            # Note: You can add logic here to explicitly delete the old picture if needed, 
            # but usually Django handles replacement automatically.
            
            user_instance.save() # Save the CustomUser changes
            
            # --- 2. Save the UserProfile fields ---
            # The ModelForm save() method handles bio, skills, and certifications
            form.save() 
            
            messages.success(request, 'Your profile has been updated!')
            return redirect('accounts:profile')
    
    else:
        # For GET request, initialize the form with data from BOTH models
        initial_data = {
            # Initial data for CustomUser fields (which are manually defined on the form)
            'first_name': user_instance.first_name,
            'last_name': user_instance.last_name,
            'phone_number': user_instance.phone_number,
            'department': user_instance.department,
            'position': user_instance.position,
            'date_of_birth': user_instance.date_of_birth,
            'profile_picture': user_instance.profile_picture # Used to pre-populate the file field (though often ignored by browsers)
        }
        
        # Pass the initial data AND the UserProfile instance 
        form = UserProfileForm(initial=initial_data, instance=profile_instance)

    return render(request, 'accounts/edit_profile.html', {'form': form})
def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def send_verification_email(request):
    """Send email verification link to user"""
    user = request.user
    
    # Check if already verified
    if user.email_verified:
        messages.info(request, 'Your email is already verified!')
        return redirect('accounts:profile')
    
    # Generate verification token
    token = get_random_string(64)
    user.email_verification_token = token
    user.save()
    
    # Build verification URL
    verification_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'token': token})
    )
    
    # Email subject and message
    subject = 'Verify Your Email - ProTrack'
    message = f"""
Hello {user.get_full_name() or user.username},

Thank you for registering with ProTrack!

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account with ProTrack, please ignore this email.

Best regards,
The ProTrack Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, f'Verification email sent to {user.email}. Please check your inbox!')
    except Exception as e:
        messages.error(request, f'Failed to send email. Please try again later. Error: {str(e)}')
    
    return redirect('accounts:profile')

@login_required
def verify_email(request, token):
    """Verify user's email with token"""
    user = request.user
    
    if user.email_verification_token == token:
        user.email_verified = True
        user.email_verification_token = ''  # Clear the token
        user.save()
        messages.success(request, '✅ Your email has been verified successfully!')
    else:
        messages.error(request, 'Invalid or expired verification link.')
    
    return redirect('accounts:profile')

# Create your views here.
