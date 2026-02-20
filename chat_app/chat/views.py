from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from accounts.models import User
from .models import Message


@login_required
def user_list(request):
    users = list(User.objects.exclude(id=request.user.id).annotate(
        unread_count=Count(
            'sent_messages',
            filter=Q(sent_messages__receiver=request.user, sent_messages__is_read=False)
        )
    ))
    for user in users:
        user.unread_count_display = '99+' if user.unread_count > 99 else str(user.unread_count)
    return render(request, 'user_list.html', {'users': users})


@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    # Mark incoming unread messages as read when opening chat
    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    messages = Message.objects.filter(
        sender=request.user, receiver=other_user
    ) | Message.objects.filter(
        sender=other_user, receiver=request.user
    )
    # Exclude messages the current user deleted only for themselves
    messages = messages.exclude(
        Q(deleted_by_sender=True, sender_id=request.user.id) |
        Q(deleted_by_receiver=True, receiver_id=request.user.id)
    )
    messages = list(messages.order_by('timestamp'))
    for msg in messages:
        msg.is_mine = (msg.sender_id == request.user.id)

    # Consistent room name regardless of who initiates
    room_name = f"{min(request.user.id, other_user.id)}_{max(request.user.id, other_user.id)}"

    return render(request, 'chat.html', {
        'other_user': other_user,
        'messages': messages,
        'room_name': room_name,
    })
