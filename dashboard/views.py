# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.db.models import Count
# from accounts.models import CustomUser
# from django.core.exceptions import PermissionDenied

# @login_required
# def dashboard(request):
#     user = request.user
    
#     if user.user_type == 'admin':
#     # Dashboard statistics
#         context = {
#             'user': user,
#             'total_users': CustomUser.objects.count(),
#             'total_students': CustomUser.objects.filter(user_type='student').count(),
#             'total_employees': CustomUser.objects.filter(user_type='employee').count(),
#             'total_admins': CustomUser.objects.filter(user_type='admin').count(),
#         }
#      elif user.user_type in ['student', 'employee']:
#         # Regular users see limited statistics
#         context = {
#             'user': user,
#             'total_users': None,  # Hidden from regular users
#             'total_students': None,
#             'total_employees': None,
#             'total_admins': None,
#         }
#     else:
#         # Invalid user type - deny access
#         raise PermissionDenied

#     return render(request, 'dashboard/dashboard.html', context)

# @login_required
# def training(request):
#     return render(request, 'dashboard/training.html')

# @login_required
# def certifications(request):
#     return render(request, 'dashboard/certifications.html')


# # Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.core.exceptions import PermissionDenied
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
    # RBAC: Check if user has access to training
    if request.user.user_type not in ['student', 'employee', 'admin']:
        raise PermissionDenied
    return render(request, 'dashboard/training.html')

@login_required
def certifications(request):
    # RBAC: Check if user has access to certifications
    if request.user.user_type not in ['student', 'employee', 'admin']:
        raise PermissionDenied
    return render(request, 'dashboard/certifications.html')