
from django.core.management.base import BaseCommand
from dashboard.models import Notification
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Remove test notifications and keep only real notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete ALL notifications (use with caution)',
        )
        parser.add_argument(
            '--test-only',
            action='store_true',
            help='Delete only test notifications (default)',
        )

    def handle(self, *args, **options):
        self.stdout.write('🧹 Cleaning up notifications...\n')
        
        if options['all']:
            # Delete all notifications
            if input('⚠️  Delete ALL notifications? (yes/no): ').lower() == 'yes':
                count = Notification.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {count} notifications'))
            else:
                self.stdout.write(self.style.WARNING('❌ Cancelled'))
                return
        else:
            # Delete test notifications (default)
            # Test notifications typically have generic messages
            test_keywords = [
                'Welcome to ProTrack!',
                'Thank you for joining',
                'New Feature: Notifications',
                'Complete Your Profile',
                "Don't forget to complete",
            ]
            
            deleted_count = 0
            for keyword in test_keywords:
                count = Notification.objects.filter(
                    message__icontains=keyword
                ).delete()[0]
                deleted_count += count
                if count > 0:
                    self.stdout.write(f'  Deleted {count} notifications containing "{keyword}"')
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Total deleted: {deleted_count} test notifications'))
            
            # Show remaining notification count
            remaining = Notification.objects.count()
            self.stdout.write(f'📊 Remaining notifications: {remaining}')
