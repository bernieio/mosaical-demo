
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal
import json

class NotificationManager:
    """Handle real-time notifications for users"""
    
    @staticmethod
    def create_notification(user, notification_type, title, message, data=None):
        """Create a notification for a user"""
        notification = {
            'id': f"{user.id}_{timezone.now().timestamp()}",
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': timezone.now().isoformat(),
            'read': False
        }
        
        # Store in cache (Redis would be better for production)
        cache_key = f"notifications:{user.id}"
        notifications = cache.get(cache_key, [])
        notifications.insert(0, notification)
        
        # Keep only last 50 notifications
        notifications = notifications[:50]
        cache.set(cache_key, notifications, timeout=86400)  # 24 hours
        
        return notification
    
    @staticmethod
    def get_user_notifications(user, unread_only=False):
        """Get notifications for a user"""
        cache_key = f"notifications:{user.id}"
        notifications = cache.get(cache_key, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n['read']]
        
        return notifications
    
    @staticmethod
    def mark_as_read(user, notification_id):
        """Mark notification as read"""
        cache_key = f"notifications:{user.id}"
        notifications = cache.get(cache_key, [])
        
        for notification in notifications:
            if notification['id'] == notification_id:
                notification['read'] = True
                break
        
        cache.set(cache_key, notifications, timeout=86400)
    
    @staticmethod
    def notify_yield_received(user, nft, amount):
        """Notify user about yield received"""
        return NotificationManager.create_notification(
            user=user,
            notification_type='YIELD_RECEIVED',
            title='Yield Received!',
            message=f'Received {amount:.6f} vBTC yield from {nft.collection.name} #{nft.token_id}',
            data={'nft_id': nft.id, 'amount': str(amount)}
        )
    
    @staticmethod
    def notify_loan_risk(user, loan, risk_level):
        """Notify user about loan risk"""
        messages = {
            'WARNING': f'Your loan #{loan.id} is approaching liquidation threshold',
            'DANGER': f'Your loan #{loan.id} is at high risk of liquidation',
            'LIQUIDATION': f'Your loan #{loan.id} has been liquidated'
        }
        
        return NotificationManager.create_notification(
            user=user,
            notification_type='LOAN_RISK',
            title=f'Loan Risk Alert - {risk_level}',
            message=messages.get(risk_level, 'Loan status update'),
            data={'loan_id': loan.id, 'risk_level': risk_level}
        )
    
    @staticmethod
    def notify_dpo_sale(buyer, seller, dpo_token):
        """Notify about DPO token sale"""
        # Notify buyer
        NotificationManager.create_notification(
            user=buyer,
            notification_type='DPO_PURCHASE',
            title='DPO Token Purchased',
            message=f'Successfully purchased {dpo_token.ownership_percentage}% of {dpo_token.original_nft.collection.name} #{dpo_token.original_nft.token_id}',
            data={'dpo_id': dpo_token.id}
        )
        
        # Notify seller
        NotificationManager.create_notification(
            user=seller,
            notification_type='DPO_SALE',
            title='DPO Token Sold',
            message=f'Your DPO token sold for {dpo_token.current_price:.6f} vBTC',
            data={'dpo_id': dpo_token.id}
        )
