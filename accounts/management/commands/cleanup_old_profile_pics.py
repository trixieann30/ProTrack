from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Clear old local profile picture paths'

    def handle(self, *args, **options):
        # Find users with local profile pictures but no Supabase URL
        users_with_old_pics = CustomUser.objects.filter(
            profile_picture__isnull=False
        ).exclude(profile_picture='')
        
        count = 0
        for user in users_with_old_pics:
            # If they don't have a Supabase URL, clear the old local path
            if not user.profile_picture_url:
                self.stdout.write(f"Clearing old profile pic for user {user.username}")
                user.profile_picture = None
                user.save()
                count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Cleared {count} old profile picture paths')
        )