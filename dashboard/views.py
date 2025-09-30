from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.models import CustomUser

@login_required
def dashboard(request):
    user = request.user
    
    # Dashboard statistics
    context = {
        'user': user,
        'total_users': CustomUser.objects.count(),
        'total_students': CustomUser.objects.filter(user_type='student').count(),
        'total_employees': CustomUser.objects.filter(user_type='employee').count(),
        'total_admins': CustomUser.objects.filter(user_type='admin').count(),
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def training(request):
    return render(request, 'dashboard/training.html')

@login_required
def certifications(request):
    return render(request, 'dashboard/certifications.html')

# Create your views here.
