
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .notifications import NotificationManager

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return
            
        self.user_id = self.scope["user"].id
        self.group_name = f"notifications_{self.user_id}"
        
        # Join notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send existing notifications
        notifications = await self.get_user_notifications()
        await self.send(text_data=json.dumps({
            'type': 'notification_list',
            'notifications': notifications
        }))
    
    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data['type'] == 'mark_read':
            notification_id = data['notification_id']
            await self.mark_notification_read(notification_id)
    
    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification']
        }))
    
    @database_sync_to_async
    def get_user_notifications(self):
        user = User.objects.get(id=self.user_id)
        return NotificationManager.get_user_notifications(user)
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        user = User.objects.get(id=self.user_id)
        NotificationManager.mark_as_read(user, notification_id)
