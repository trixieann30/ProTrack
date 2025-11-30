from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from dashboard.models import Notification


class Command(BaseCommand):
    help = 'Create welcome notifications for all existing users'

    def handle(self, *args, **kwargs):
        self.stdout.write('🎉 Creating welcome notifications for all users...\n')
        
        # Get all active users
        users = CustomUser.objects.filter(is_active=True)
        created_count = 0
        skipped_count = 0
        
        for user in users:
            # Check if user already has a welcome notification
            existing_welcome = Notification.objects.filter(
                user=user,
                notification_type='system',
                title='Welcome to ProTrack!'
            ).exists()
            
            if existing_welcome:
                self.stdout.write(f'  ⏭️  Skipped {user.username} - already has welcome notification')
                skipped_count += 1
                continue
            
            # Create welcome notification
            Notification.objects.create(
                user=user,
                notification_type='system',
                title='Welcome to ProTrack!',
                message=f'Hello {user.get_full_name() or user.username}! Welcome to ProTrack - your skills and training management platform. Get started by browsing our training catalog and enrolling in courses that match your interests.',
                link='/dashboard/training/catalog/',
                is_read=False
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ Created welcome notification for {user.username}')
            )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'\n✓ Summary:'))
        self.stdout.write(f'  • Total users: {users.count()}')
        self.stdout.write(f'  • Notifications created: {created_count}')
        self.stdout.write(f'  • Already had notification: {skipped_count}')
        self.stdout.write(self.style.SUCCESS('\n✓ Done!\n'))
