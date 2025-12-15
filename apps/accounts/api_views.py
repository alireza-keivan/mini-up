"""
API Views for Accounts App
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from apps.content.services import NotificationService


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@require_GET
def get_notifications_api(request):
    """
    API: دریافت لیست اعلان‌ها
    GET /accounts/api/notifications/
    Query params:
        - unread_only: فقط خوانده نشده‌ها (true/false)
        - limit: محدودیت تعداد (default: 20)
        - offset: شروع از (default: 0)
    """
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    limit = min(int(request.GET.get('limit', 20)), 100)
    offset = int(request.GET.get('offset', 0))
    
    notifications = NotificationService.list_all(request.user)
    
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    total_count = notifications.count()
    notifications = notifications[offset:offset+limit]
    
    data = {
        'success': True,
        'total_count': total_count,
        'unread_count': NotificationService.get_unread_count(request.user),
        'notifications': [
            {
                'id': str(n.id),
                'title': n.title,
                'message': n.message,
                'type': n.type,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
                'read_at': n.read_at.isoformat() if n.read_at else None,
            }
            for n in notifications
        ]
    }
    
    return JsonResponse(data)


@login_required
@require_GET
def get_unread_count_api(request):
    """
    API: دریافت تعداد اعلان‌های خوانده نشده
    GET /accounts/api/notifications/unread-count/
    """
    unread_count = NotificationService.get_unread_count(request.user)
    
    return JsonResponse({
        'success': True,
        'unread_count': unread_count
    })


@login_required
@require_POST
def mark_notification_read_api(request):
    """
    API: علامت‌گذاری اعلان به عنوان خوانده شده
    POST /accounts/api/notifications/mark-read/
    Body: { "notification_id": "uuid" }
    """
    import json
    
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return JsonResponse({
                'success': False,
                'message': 'شناسه اعلان الزامی است'
            }, status=400)
        
        success = NotificationService.mark_as_read(
            request.user,
            notification_ids=[notification_id]
        )
        
        return JsonResponse({
            'success': success > 0,
            'message': 'اعلان به عنوان خوانده شده علامت‌گذاری شد' if success else 'اعلان یافت نشد'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'فرمت JSON نامعتبر است'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def mark_all_notifications_read_api(request):
    """
    API: علامت‌گذاری همه اعلان‌ها به عنوان خوانده شده
    POST /accounts/api/notifications/mark-all-read/
    """
    try:
        count = NotificationService.mark_as_read(request.user)
        
        return JsonResponse({
            'success': True,
            'message': f'{count} اعلان به عنوان خوانده شده علامت‌گذاری شد',
            'marked_count': count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def delete_notification_api(request):
    """
    API: حذف اعلان
    POST /accounts/api/notifications/delete/
    Body: { "notification_id": "uuid" }
    """
    import json
    
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return JsonResponse({
                'success': False,
                'message': 'شناسه اعلان الزامی است'
            }, status=400)
        
        success = NotificationService.delete_notification(notification_id, request.user)
        
        return JsonResponse({
            'success': success,
            'message': 'اعلان حذف شد' if success else 'اعلان یافت نشد'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'فرمت JSON نامعتبر است'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)