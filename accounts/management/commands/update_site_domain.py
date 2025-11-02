from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Update the Site domain for production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default='protrackskillmanagement.onrender.com',
            help='Domain name to set (default: protrackskillmanagement.onrender.com)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default='ProTrack Production',
            help='Site display name (default: ProTrack Production)'
        )

    def handle(self, *args, **options):
        domain = options['domain']
        name = options['name']
        
        try:
            # Get the current site (usually ID=1)
            site = Site.objects.get_current()
            old_domain = site.domain
            
            site.domain = domain
            site.name = name
            site.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated site domain from "{old_domain}" to "{domain}"'
                )
            )
            self.stdout.write(f'Site name: {name}')
            self.stdout.write(f'Site ID: {site.id}')
            
        except Site.DoesNotExist:
            # Create new site if none exists
            site = Site.objects.create(
                id=1,
                domain=domain,
                name=name
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created new site with domain "{domain}"'
                )
            )
        
        # Verify
        current_site = Site.objects.get_current()
        self.stdout.write('\nCurrent site configuration:')
        self.stdout.write(f'  Domain: {current_site.domain}')
        self.stdout.write(f'  Name: {current_site.name}')
        self.stdout.write(f'  ID: {current_site.id}')
