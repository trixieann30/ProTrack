from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from dashboard.models import Notification

User = get_user_model()

@receiver(post_save, sender=User)
def create_welcome_notifications(sender, instance, created, **kwargs):
    """
    Automatically create welcome notifications for new users
    """
    if created:
        # Welcome notification
        Notification.objects.create(
            user=instance,
            notification_type='announcement',
            title='Welcome to ProTrack!',
            message=f'Hello {instance.get_full_name() or instance.username}! Thank you for joining our training platform. Explore available courses and start learning!',
            link='/dashboard/training/catalog/'
        )
        
        # Profile completion reminder
        Notification.objects.create(
            user=instance,
            notification_type='reminder',
            title='Complete Your Profile',
            message='Don\'t forget to complete your profile to get personalized course recommendations.',
            link='/accounts/profile/edit/'
        )
        
        # Feature announcement
        Notification.objects.create(
            user=instance,
            notification_type='system',
            title='Explore ProTrack Features',
            message='Discover training courses, track your progress, earn certificates, and more!',
            link='/dashboard/'
        )