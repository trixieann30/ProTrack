from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup Google OAuth configuration'

    def handle(self, *args, **options):
        # Update or create site
        site, created = Site.objects.get_or_create(
            id=settings.SITE_ID,
            defaults={
                'domain': '127.0.0.1:8000',
                'name': 'ProTrack'
            }
        )
        
        if not created:
            site.domain = '127.0.0.1:8000'
            site.name = 'ProTrack'
            site.save()
            self.stdout.write(self.style.SUCCESS(f'Updated site: {site.domain}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created site: {site.domain}'))

        # Check if Google social app exists
        google_app = SocialApp.objects.filter(provider='google').first()
        
        if google_app:
            self.stdout.write(self.style.WARNING('Google OAuth app already exists!'))
            self.stdout.write(f'Client ID: {google_app.client_id[:20]}...')
        else:
            self.stdout.write(self.style.WARNING('Google OAuth app not found!'))
            self.stdout.write(self.style.WARNING('Please add it manually in Django admin:'))
            self.stdout.write('1. Go to http://127.0.0.1:8000/admin/')
            self.stdout.write('2. Navigate to Social applications')
            self.stdout.write('3. Click "Add social application"')
            self.stdout.write('4. Fill in:')
            self.stdout.write('   - Provider: Google')
            self.stdout.write('   - Name: Google OAuth')
            self.stdout.write('   - Client ID: [from Google Cloud Console]')
            self.stdout.write('   - Secret key: [from Google Cloud Console]')
            self.stdout.write('   - Sites: Select 127.0.0.1:8000')
