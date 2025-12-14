# apps/consulting/views.py

"""
Views for ticket support system
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q

from .models import ConsultingCategory, SupportTicket, TicketMessage, TicketAttachment


@login_required
def ticket_list(request):
    """
    User ticket list page
    GET /consulting/tickets/
    """
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'in_progress', 'answered', 'closed']:
        tickets = tickets.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        tickets = tickets.filter(
            Q(ticket_id__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(initial_message__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'consulting/ticket_list.html', context)


@login_required
def ticket_detail(request, ticket_id):
    """
    Ticket detail and chat page
    GET /consulting/tickets/<ticket_id>/
    """
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    # Get messages
    messages_qs = ticket.messages.select_related('sender').prefetch_related('attachments').order_by('created_at')
    
    # Mark staff messages as read
    unread_staff_messages = messages_qs.filter(is_staff_reply=True, is_read=False)
    for msg in unread_staff_messages:
        msg.mark_as_read()
    
    context = {
        'ticket': ticket,
        'messages': messages_qs,
    }
    
    return render(request, 'consulting/ticket_detail.html', context)


@login_required
def ticket_create(request):
    """
    Create new ticket page
    GET/POST /consulting/tickets/create/
    """
    categories = ConsultingCategory.objects.filter(is_active=True)
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        subject = request.POST.get('subject')
        initial_message = request.POST.get('message')
        priority = request.POST.get('priority', 'medium')
        
        # Validation
        if not all([category_id, subject, initial_message]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'consulting/ticket_create.html', {'categories': categories})
        
        try:
            category = ConsultingCategory.objects.get(id=category_id, is_active=True)
        except ConsultingCategory.DoesNotExist:
            messages.error(request, 'Invalid category selected.')
            return render(request, 'consulting/ticket_create.html', {'categories': categories})
        
        # Create ticket
        ticket = SupportTicket.objects.create(
            user=request.user,
            category=category,
            subject=subject,
            initial_message=initial_message,
            priority=priority
        )
        
        messages.success(request, f'Ticket #{ticket.ticket_id} created successfully.')
        return redirect('consulting:ticket_detail', ticket_id=ticket.ticket_id)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'consulting/ticket_create.html', context)


@login_required
@require_POST
def ticket_message_create(request, ticket_id):
    """
    Send message in ticket
    POST /consulting/tickets/<ticket_id>/message/
    """
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    # Check ticket status
    if ticket.is_closed:
        messages.error(request, 'This ticket is closed. Please reopen it to send a message.')
        return redirect('consulting:ticket_detail', ticket_id=ticket.ticket_id)
    
    message_text = request.POST.get('message')
    if not message_text or not message_text.strip():
        messages.error(request, 'Message cannot be empty.')
        return redirect('consulting:ticket_detail', ticket_id=ticket.ticket_id)
    
    # Create message
    message = TicketMessage.objects.create(
        ticket=ticket,
        sender=request.user,
        message=message_text.strip(),
        is_staff_reply=False
    )
    
    # Upload file if exists
    uploaded_file = request.FILES.get('attachment')
    if uploaded_file:
        try:
            TicketAttachment.objects.create(
                message=message,
                file=uploaded_file
            )
        except Exception as e:
            messages.warning(request, f'Message sent but attachment failed: {str(e)}')
    
    messages.success(request, 'Message sent successfully.')
    return redirect('consulting:ticket_detail', ticket_id=ticket.ticket_id)


@login_required
@require_POST
def ticket_close(request, ticket_id):
    """
    Close ticket
    POST /consulting/tickets/<ticket_id>/close/
    """
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    if ticket.is_closed:
        messages.info(request, 'This ticket is already closed.')
    else:
        ticket.close()
        messages.success(request, 'Ticket closed successfully.')
    
    return redirect('consulting:ticket_detail', ticket_id=ticket.ticket_id)


@login_required
@require_POST
def ticket_reopen(request, ticket_id):
    """
    Reopen closed ticket
    POST /consulting/tickets/<ticket_id>/reopen/
    """
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    if not ticket.is_closed:
        messages.info(request, 'This ticket is already open.')
    else:
        ticket.reopen()
        messages.success(request, 'Ticket reopened successfully.')
    
    return redirect('consulting:ticket_detail', ticket_id=ticket.ticket_id)


# AJAX Views
@login_required
def ticket_check_new_messages(request, ticket_id):
    """
    Check for new ticket messages (AJAX)
    GET /consulting/tickets/<ticket_id>/check-messages/
    """
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    last_message_id = request.GET.get('last_message_id')
    
    if last_message_id:
        new_messages = ticket.messages.filter(id__gt=last_message_id).order_by('created_at')
    else:
        new_messages = ticket.messages.order_by('-created_at')[:1]
    
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.get_full_name() or msg.sender.phone,
            'message': msg.message,
            'is_staff_reply': msg.is_staff_reply,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'attachments': [
                {
                    'url': att.file.url,
                    'filename': att.original_filename
                }
                for att in msg.attachments.all()
            ]
        })
    
    return JsonResponse({
        'has_new_messages': len(messages_data) > 0,
        'messages': messages_data,
        'ticket_status': ticket.status
    })
