# apps/content/context_processors.py

"""
Context processors for Content app
"""

from .services import NotificationService


def notifications(request):
    """
    Add notification count to all templates
    """
    if request.user.is_authenticated:
        unread_count = NotificationService.get_unread_count(request.user)
        return {
            'unread_notifications_count': unread_count,
        }
    return {
        'unread_notifications_count': 0,
    }
