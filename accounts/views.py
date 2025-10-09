from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import CustomUser, UserProfile
from django.contrib.auth import logout

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
                return redirect('dashboard:dashboard')  # Redirect to dashboard
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
# Create your views here.
