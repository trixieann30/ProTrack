"""
Management command to notify users about their incomplete courses.
Run this command daily via a scheduled task/cron job:
    python manage.py notify_incomplete_courses
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.urls import reverse
from dashboard.models import Enrollment, Notification
from accounts.models import NotificationPreference


class Command(BaseCommand):
    help = 'Send notifications to users about their incomplete courses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Notify about courses inactive for more than N days (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be notified without actually creating notifications'
        )

    def handle(self, *args, **options):
        days_threshold = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Looking for incomplete courses inactive for {days_threshold}+ days...")
        
        cutoff_date = timezone.now() - timedelta(days=days_threshold)
        
        # Find enrollments that are in progress but haven't been updated recently
        incomplete_enrollments = Enrollment.objects.filter(
            status__in=['enrolled', 'in_progress'],
            progress_percentage__lt=100,
            progress_percentage__gt=0,  # They started but didn't finish
        ).select_related('user', 'course')
        
        # Also check for enrollments where user hasn't made progress
        stale_enrollments = Enrollment.objects.filter(
            status__in=['enrolled', 'in_progress'],
            enrolled_date__lt=cutoff_date,
        ).select_related('user', 'course')
        
        # Combine both querysets
        all_incomplete = incomplete_enrollments | stale_enrollments
        all_incomplete = all_incomplete.distinct()
        
        notified_count = 0
        skipped_count = 0
        
        for enrollment in all_incomplete:
            user = enrollment.user
            course = enrollment.course
            
            # Check if user has reminder notifications enabled
            try:
                prefs = NotificationPreference.objects.get(user=user)
                if not prefs.notify_on_reminder:
                    skipped_count += 1
                    continue
            except NotificationPreference.DoesNotExist:
                pass  # Default to sending notifications
            
            # Check if we already sent a reminder recently (within 7 days)
            recent_reminder = Notification.objects.filter(
                user=user,
                notification_type='reminder',
                related_enrollment=enrollment,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if recent_reminder:
                skipped_count += 1
                continue
            
            # Calculate progress
            total_materials = course.materials.filter(is_required=True).count()
            completed_materials = enrollment.completed_materials.filter(is_required=True).count()
            
            if total_materials > 0:
                progress = round((completed_materials / total_materials) * 100)
            else:
                progress = enrollment.progress_percentage
            
            # Create the notification
            title = f"Continue Your Training: {course.title}"
            message = f"You've made {progress}% progress in \"{course.title}\". Keep going to complete your training!"
            link = reverse('dashboard:course_detail', args=[course.id])
            
            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] Would notify {user.username}: {title} ({progress}%)"
                )
            else:
                Notification.objects.create(
                    user=user,
                    notification_type='reminder',
                    title=title,
                    message=message,
                    link=link,
                    related_enrollment=enrollment
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Notified {user.username}: {course.title} ({progress}%)")
                )
            
            notified_count += 1
        
        self.stdout.write("")
        self.stdout.write("=" * 50)
        if dry_run:
            self.stdout.write(f"DRY RUN COMPLETE: Would notify {notified_count} users")
        else:
            self.stdout.write(self.style.SUCCESS(f"Notified {notified_count} users about incomplete courses"))
        self.stdout.write(f"Skipped {skipped_count} (already notified or preferences disabled)")
