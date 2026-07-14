#!/usr/bin/env python
"""
Script to create initial social media links
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings.dev')
django.setup()

from apps.core.models import SocialMediaLinks

# Create or update social media links
social, created = SocialMediaLinks.objects.get_or_create(
    id=1,
    defaults={
        'instagram': 'minigame.shop',
        'telegram': 'miniupir',
        'youtube': 'minigame_org',
        'is_active': True
    }
)

if not created:
    # Update existing record
    social.instagram = 'minigame.shop'
    social.telegram = 'miniupir'
    social.youtube = 'minigame_org'
    social.is_active = True
    social.save()
    print('✅ Social media links updated successfully!')
else:
    print('✅ Social media links created successfully!')

print(f'\n📱 Social Media Links:')
print(f'   Instagram: {social.instagram_url}')
print(f'   Telegram: {social.telegram_url}')
print(f'   YouTube: {social.youtube_url}')
