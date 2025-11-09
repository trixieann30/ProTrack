from django.contrib import admin
from .models import TrainingModule

@admin.register(TrainingModule)
class TrainingModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'duration', 'status', 'updated_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description')
    actions = ['archive_modules', 'restore_modules']

    def archive_modules(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f"{updated} module(s) archived successfully.")
    archive_modules.short_description = "Archive selected modules"

    def restore_modules(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f"{updated} module(s) restored successfully.")
    restore_modules.short_description = "Restore selected modules"


# Register your models here.
