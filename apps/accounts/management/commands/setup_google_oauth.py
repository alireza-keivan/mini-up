"""
Management command to setup Google OAuth Social App
Usage: python manage.py setup_google_oauth --client-id YOUR_CLIENT_ID --secret YOUR_SECRET
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Setup Google OAuth Social Application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Google OAuth Client ID',
            required=True
        )
        parser.add_argument(
            '--secret',
            type=str,
            help='Google OAuth Client Secret',
            required=True
        )
        parser.add_argument(
            '--name',
            type=str,
            default='Google',
            help='Name for the social app (default: Google)'
        )

    def handle(self, *args, **options):
        client_id = options['client_id']
        secret = options['secret']
        name = options['name']

        # Get or create the current site
        current_site = Site.objects.get_current()
        
        # Check if Google app already exists
        google_app = SocialApp.objects.filter(provider='google').first()
        
        if google_app:
            self.stdout.write(
                self.style.WARNING(f'Google Social App already exists: {google_app.name}')
            )
            update = input('Do you want to update it? (yes/no): ')
            if update.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.WARNING('Aborted'))
                return
            
            google_app.client_id = client_id
            google_app.secret = secret
            google_app.name = name
            google_app.save()
            google_app.sites.add(current_site)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Updated Google Social App: {google_app.name}')
            )
        else:
            # Create new social app
            google_app = SocialApp.objects.create(
                provider='google',
                name=name,
                client_id=client_id,
                secret=secret
            )
            google_app.sites.add(current_site)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Google Social App: {google_app.name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nGoogle OAuth is now configured!')
        )
        self.stdout.write(
            f'  Provider: google'
        )
        self.stdout.write(
            f'  Client ID: {client_id[:20]}...'
        )
        self.stdout.write(
            f'  Site: {current_site.domain}'
        )
        self.stdout.write(
            f'\nYou can now use Google login at: /accounts/login/google/'
        )
