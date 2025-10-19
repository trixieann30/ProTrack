# Protrack/dashboard/admin.py
from django.contrib import admin
from .models import TrainingCategory, TrainingCourse, TrainingSession, Enrollment

@admin.register(TrainingCategory)
class TrainingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at', 'course_count']
    search_fields = ['name', 'description']
    list_per_page = 20
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Number of Courses'


@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'instructor', 'level', 'duration_hours', 
                    'status', 'enrolled_count', 'created_at']
    list_filter = ['status', 'level', 'category', 'created_at']
    search_fields = ['title', 'description', 'instructor']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'instructor', 'thumbnail')
        }),
        ('Course Details', {
            'fields': ('duration_hours', 'level', 'max_participants', 'status')
        }),
        ('Additional Information', {
            'fields': ('prerequisites', 'learning_outcomes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def enrolled_count(self, obj):
        return obj.enrollments.filter(status__in=['enrolled', 'in_progress']).count()
    enrolled_count.short_description = 'Active Enrollments'


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['session_name', 'course', 'start_date', 'end_date', 
                    'location', 'is_online', 'enrollment_count']
    list_filter = ['is_online', 'start_date', 'course__category']
    search_fields = ['session_name', 'course__title', 'location']
    date_hierarchy = 'start_date'
    list_per_page = 20
    
    fieldsets = (
        ('Session Information', {
            'fields': ('course', 'session_name', 'is_online')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time')
        }),
        ('Location', {
            'fields': ('location', 'notes')
        }),
    )
    
    def enrollment_count(self, obj):
        return obj.enrollments.count()
    enrollment_count.short_description = 'Enrollments'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'status', 'progress_percentage', 
                    'score', 'enrolled_date', 'completion_date', 'assigned_by']
    list_filter = ['status', 'enrolled_date', 'completion_date', 'course__category']
    search_fields = ['user__username', 'user__email', 'course__title']
    readonly_fields = ['enrolled_date']
    date_hierarchy = 'enrolled_date'
    list_per_page = 20
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('user', 'course', 'session', 'status', 'assigned_by')
        }),
        ('Progress Tracking', {
            'fields': ('start_date', 'completion_date', 'progress_percentage', 'score')
        }),
        ('Additional Information', {
            'fields': ('feedback', 'notes', 'enrolled_date')
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_in_progress', 'cancel_enrollments']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status='completed',
            completion_date=timezone.now().date(),
            progress_percentage=100
        )
        self.message_user(request, f'{updated} enrollment(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} enrollment(s) marked as in progress.')
    mark_as_in_progress.short_description = 'Mark selected as in progress'
    
    def cancel_enrollments(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} enrollment(s) cancelled.')
    cancel_enrollments.short_description = 'Cancel selected enrollments'