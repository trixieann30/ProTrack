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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser

@login_required
def dashboard(request):
    user = request.user
    
    # RBAC: Role-based context
    if user.user_type == 'admin':
        # Admins see all statistics
        context = {
            'user': user,
            'total_users': CustomUser.objects.count(),
            'total_students': CustomUser.objects.filter(user_type='student').count(),
            'total_employees': CustomUser.objects.filter(user_type='employee').count(),
            'total_admins': CustomUser.objects.filter(user_type='admin').count(),
        }
    elif user.user_type in ['student', 'employee']:
        # Regular users see limited statistics
        context = {
            'user': user,
            'total_users': None,  # Hidden from regular users
            'total_students': None,
            'total_employees': None,
            'total_admins': None,
        }
    else:
        # Invalid user type - deny access
        raise PermissionDenied
    
    return render(request, 'dashboard/dashboard.html', context)

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