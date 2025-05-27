
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class AuditLog(models.Model):
    AUDIT_ACTIONS = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('DEPOSIT_NFT', 'NFT Deposit'),
        ('WITHDRAW_NFT', 'NFT Withdrawal'),
        ('CREATE_LOAN', 'Loan Creation'),
        ('REPAY_LOAN', 'Loan Repayment'),
        ('LIQUIDATION', 'Loan Liquidation'),
        ('DPO_TRADE', 'DPO Token Trade'),
        ('ADMIN_ACTION', 'Admin Action'),
        ('FAUCET_CLAIM', 'Faucet Claim'),
        ('SWAP_COLLATERAL', 'Collateral Swap'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=AUDIT_ACTIONS)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"

class AuditLogger:
    """Utility class for audit logging"""
    
    @staticmethod
    def log_action(user, action, request, details=None, success=True, error=None):
        """Log an audit action"""
        AuditLog.objects.create(
            user=user,
            action=action,
            details=details or {},
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=success,
            error_message=error or ''
        )
    
    @staticmethod
    def log_financial_transaction(user, transaction_type, amount, nft=None, loan=None, request=None):
        """Log financial transactions with detailed info"""
        details = {
            'transaction_type': transaction_type,
            'amount': str(amount),
        }
        
        if nft:
            details['nft'] = {
                'id': nft.id,
                'collection': nft.collection.name,
                'token_id': nft.token_id,
                'estimated_value': str(nft.estimated_value)
            }
        
        if loan:
            details['loan'] = {
                'id': loan.id,
                'principal': str(loan.principal_amount),
                'current_debt': str(loan.current_debt),
                'ltv_ratio': str(loan.ltv_ratio)
            }
        
        AuditLogger.log_action(user, transaction_type, request, details)
