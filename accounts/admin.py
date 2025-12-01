from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile
from .models import NotificationPreference
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_type', 'department', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'department', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'profile_picture', 'date_of_birth', 'department', 'position')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'department')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user__email', 'user__user_type']
    search_fields = ['user__username', 'user__email']
    list_filter = ['user__user_type']

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'email_on_enrollment',
        'notify_on_enrollment',
    ]
    search_fields = ['user__username', 'user__email']
    list_filter = ['email_on_enrollment']
    
    fieldsets = (
        ('Email Notifications', {
            'fields': (
                'email_on_enrollment',
                'email_on_completion',
                'email_on_certificate',
                'email_on_assignment',
                'email_on_reminder',
            )
        }),
        ('In-App Notifications', {
            'fields': (
                'notify_on_enrollment',
                'notify_on_completion',
                'notify_on_certificate',
                'notify_on_assignment',
                'notify_on_reminder',
                'notify_on_announcement',
            )
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

# Register your models here.
