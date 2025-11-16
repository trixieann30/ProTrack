from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from dashboard.models import Notification

class Command(BaseCommand):
    help = 'Create test notifications for all users'
    
    def handle(self, *args, **kwargs):
        users = CustomUser.objects.filter(is_active=True)
        
        for user in users:
            # Create sample notifications
            Notification.objects.create(
                user=user,
                notification_type='enrollment',
                title='Welcome to ProTrack!',
                message='Thank you for joining our training platform. Explore available courses and start learning!',
                link='/dashboard/training/catalog/'
            )
            
            Notification.objects.create(
                user=user,
                notification_type='announcement',
                title='New Feature: Notifications',
                message='We\'ve added a notification system to keep you updated on your training progress!',
                link='/dashboard/notifications/'
            )
            
            Notification.objects.create(
                user=user,
                notification_type='reminder',
                title='Complete Your Profile',
                message='Don\'t forget to complete your profile to get personalized course recommendations.',
                link='/accounts/profile/edit/'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created test notifications for {user.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCreated notifications for {users.count()} users!')
        )

# Run with: python manage.py create_test_notifications