import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class PresenceConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        self.user = self.scope['user']
        await self.channel_layer.group_add('presence', self.channel_name)
        # Personal group so unread count updates can be pushed to this user
        await self.channel_layer.group_add(f'user_{self.user.id}', self.channel_name)
        await self.accept()

        await self.set_user_status(True)
        await self.channel_layer.group_send('presence', {
            'type': 'presence_update',
            'user_id': self.user.id,
            'is_online': True,
            'last_seen_display': 'Online',
            'last_seen_iso': None,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user.is_authenticated:
            last_seen_info = await self.set_user_status(False)
            await self.channel_layer.group_send('presence', {
                'type': 'presence_update',
                'user_id': self.user.id,
                'is_online': False,
                'last_seen_display': last_seen_info['display'],
                'last_seen_iso': last_seen_info['iso'],
            })
        await self.channel_layer.group_discard('presence', self.channel_name)
        if hasattr(self, 'user'):
            await self.channel_layer.group_discard(f'user_{self.user.id}', self.channel_name)

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence_update',
            'user_id': event['user_id'],
            'is_online': event['is_online'],
            'last_seen_display': event['last_seen_display'],
            'last_seen_iso': event.get('last_seen_iso'),
        }))

    async def unread_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'sender_id': event['sender_id'],
            'count': event['count'],
            'count_display': event['count_display'],
        }))

    @database_sync_to_async
    def set_user_status(self, is_online):
        from accounts.models import User
        updates = {'is_online': is_online}
        if not is_online:
            updates['last_seen'] = timezone.now()
        User.objects.filter(id=self.user.id).update(**updates)
        user = User.objects.get(id=self.user.id)
        return {
            'display': user.last_seen_display,
            'iso': user.last_seen.isoformat() if user.last_seen else None,
        }


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')

        if message_type == 'message':
            content = data.get('message', '').strip()
            if not content:
                return
            sender = self.scope['user']
            receiver_id = data.get('receiver_id')
            message = await self.save_message(sender.id, receiver_id, content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': content,
                    'sender_id': sender.id,
                    'sender_username': sender.username,
                    'timestamp': message.timestamp.isoformat(),
                    'message_id': message.id,
                    'is_read': message.is_read,
                }
            )

            # Notify the receiver's user_list page about the new unread message
            unread_count = await self.get_unread_count(sender.id, receiver_id)
            await self.channel_layer.group_send(
                f'user_{receiver_id}',
                {
                    'type': 'unread_count_update',
                    'sender_id': sender.id,
                    'count': unread_count,
                    'count_display': '99+' if unread_count > 99 else str(unread_count),
                }
            )

        elif message_type == 'delete_message':
            message_id = data.get('message_id')
            delete_type = data.get('delete_type')  # 'for_everyone' or 'for_me'
            success = await self.delete_message(message_id, self.scope['user'].id, delete_type)
            if success:
                if delete_type == 'for_everyone':
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'message_deleted',
                            'message_id': message_id,
                            'delete_type': 'for_everyone',
                        }
                    )
                else:
                    # Only this user's session needs to know
                    await self.send(text_data=json.dumps({
                        'type': 'message_deleted',
                        'message_id': message_id,
                        'delete_type': 'for_me',
                    }))

        elif message_type == 'read_receipt':
            message_ids = data.get('message_ids', [])
            await self.mark_messages_read(message_ids)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'message_ids': message_ids,
                }
            )

            # Update the reader's user_list page — badge should drop to 0
            reader_id = self.scope['user'].id
            sender_id = self._get_other_user_id()
            unread_count = await self.get_unread_count(sender_id, reader_id)
            await self.channel_layer.group_send(
                f'user_{reader_id}',
                {
                    'type': 'unread_count_update',
                    'sender_id': sender_id,
                    'count': unread_count,
                    'count_display': '99+' if unread_count > 99 else str(unread_count),
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'is_read': event['is_read'],
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_ids': event['message_ids'],
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
            'delete_type': event['delete_type'],
        }))

    def _get_other_user_id(self):
        """Derive the other user's ID from the room name (format: min_id_max_id)."""
        user_id = self.scope['user'].id
        ids = [int(x) for x in self.room_name.split('_')]
        return ids[0] if ids[1] == user_id else ids[1]

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        from .models import Message
        return Message.objects.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
        )

    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        from .models import Message
        Message.objects.filter(id__in=message_ids).update(is_read=True)

    @database_sync_to_async
    def delete_message(self, message_id, user_id, delete_type):
        from .models import Message
        try:
            msg = Message.objects.get(id=message_id)
            if delete_type == 'for_everyone':
                if msg.sender_id != user_id:
                    return False  # only the sender can delete for everyone
                msg.is_deleted = True
                msg.save(update_fields=['is_deleted'])
            else:
                if msg.sender_id == user_id:
                    msg.deleted_by_sender = True
                    msg.save(update_fields=['deleted_by_sender'])
                elif msg.receiver_id == user_id:
                    msg.deleted_by_receiver = True
                    msg.save(update_fields=['deleted_by_receiver'])
                else:
                    return False
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def get_unread_count(self, sender_id, receiver_id):
        from .models import Message
        return Message.objects.filter(
            sender_id=sender_id, receiver_id=receiver_id, is_read=False
        ).count()
