from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.paginator import Paginator
from accounts.models import CustomUser

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
    return render(request, 'dashboard/training.html')

@login_required
def certifications(request):
    return render(request, 'dashboard/certifications.html')

# ============ SETTINGS VIEWS ============

@login_required
def settings(request):
    """User settings page"""
    return render(request, 'dashboard/settings.html')

@login_required
def profile_settings(request):
    """Update user profile"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone_number = request.POST.get('phone_number', '')
        user.address = request.POST.get('address', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard:settings')
    
    return render(request, 'dashboard/profile_settings.html')

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'dashboard/change_password.html', {'form': form})

# ============ ADMIN CRUD OPERATIONS ============

@login_required
@user_passes_test(is_superuser)
def admin_users_list(request):
    """List all users with search and filter"""
    users = CustomUser.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Filter by user type
    user_type = request.GET.get('user_type', '')
    if user_type:
        users = users.filter(user_type=user_type)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(users, 20)  # 20 users per page
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
    """View user details"""
    user = get_object_or_404(CustomUser, id=user_id)
    context = {'selected_user': user}
    return render(request, 'dashboard/admin_user_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def admin_user_create(request):
    """Create new user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        user_type = request.POST.get('user_type', 'student')
        phone_number = request.POST.get('phone_number', '')
        is_superuser_flag = request.POST.get('is_superuser') == 'on'
        
        # Validate required fields
        if not username or not email or not password:
            messages.error(request, 'Username, email, and password are required.')
            return render(request, 'dashboard/admin_user_create.html')
        
        # Check if username exists
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'dashboard/admin_user_create.html')
        
        # Check if email exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'dashboard/admin_user_create.html')
        
        # If creating a superuser, set user_type to 'admin'
        if is_superuser_flag:
            user_type = 'admin'
        
        # Create user
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            phone_number=phone_number
        )
        
        # Set superuser status
        if is_superuser_flag:
            user.is_superuser = True
            user.is_staff = True
            user.save()
        
        messages.success(request, f'User {username} created successfully!')
        return redirect('dashboard:admin_user_detail', user_id=user.id)
    
    return render(request, 'dashboard/admin_user_create.html')

@login_required
@user_passes_test(is_superuser)
def admin_user_edit(request, user_id):
    """Edit user details"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.user_type = request.POST.get('user_type', 'student')
        user.phone_number = request.POST.get('phone_number', '')
        user.address = request.POST.get('address', '')
        user.is_active = request.POST.get('is_active') == 'on'
        
        # Handle profile picture
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('dashboard:admin_user_detail', user_id=user.id)
    
    context = {'selected_user': user}
    return render(request, 'dashboard/admin_user_edit.html', context)

@login_required
@user_passes_test(is_superuser)
def admin_user_delete(request, user_id):
    """Delete user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('dashboard:admin_users_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('dashboard:admin_users_list')
    
    context = {'selected_user': user}
    return render(request, 'dashboard/admin_user_delete.html', context)

@login_required
@user_passes_test(is_superuser)
def admin_user_toggle_status(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Prevent deactivating yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own account!')
        return redirect('dashboard:admin_user_detail', user_id=user.id)
    
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} {status} successfully!')
    return redirect('dashboard:admin_user_detail', user_id=user.id)
