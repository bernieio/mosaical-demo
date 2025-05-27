from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    vbtc_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.vbtc_balance} vBTC"

class NFTCollection(models.Model):
    name = models.CharField(max_length=200)
    game_name = models.CharField(max_length=200)
    max_ltv_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)  # %
    base_yield_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)  # % per month
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.game_name})"

class NFTVault(models.Model):
    STATUS_CHOICES = [
        ('DEPOSITED', 'Deposited'),
        ('COLLATERALIZED', 'Used as Collateral'),
        ('PARTIAL_LIQUIDATED', 'Partially Liquidated'),
        ('LIQUIDATED', 'Fully Liquidated'),
        ('WITHDRAWN', 'Withdrawn'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    collection = models.ForeignKey(NFTCollection, on_delete=models.CASCADE)
    token_id = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    estimated_value = models.DecimalField(max_digits=20, decimal_places=8)  # in vBTC
    utility_score = models.IntegerField(default=50)  # 0-100
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DEPOSITED')
    deposit_date = models.DateTimeField(auto_now_add=True)
    last_yield_date = models.DateTimeField(null=True, blank=True)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)

    class Meta:
        unique_together = ['collection', 'token_id']

    def __str__(self):
        return f"{self.collection.name} #{self.token_id} - {self.owner.username}"

class Loan(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('REPAID', 'Fully Repaid'),
        ('LIQUIDATED', 'Liquidated'),
        ('DEFAULTED', 'Defaulted'),
    ]

    borrower = models.ForeignKey(User, on_delete=models.CASCADE)
    nft_collateral = models.ForeignKey(NFTVault, on_delete=models.CASCADE)
    principal_amount = models.DecimalField(max_digits=20, decimal_places=8)  # vBTC borrowed
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # % per month
    current_debt = models.DecimalField(max_digits=20, decimal_places=8)
    ltv_ratio = models.DecimalField(max_digits=5, decimal_places=2)  # Current LTV %
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    last_interest_update = models.DateTimeField(auto_now_add=True)

    def calculate_health_factor(self):
        """Calculate health factor based on current LTV"""
        if self.current_debt == 0:
            return 100.0
        current_ltv = (self.current_debt / self.nft_collateral.estimated_value) * 100
        return float(100 - current_ltv)

    def __str__(self):
        return f"Loan #{self.id} - {self.borrower.username} - {self.principal_amount} vBTC"

class YieldRecord(models.Model):
    nft = models.ForeignKey(NFTVault, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)  # vBTC yield
    yield_date = models.DateTimeField(auto_now_add=True)
    applied_to_loan = models.ForeignKey(Loan, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Yield {self.amount} vBTC for {self.nft}"

class DPOToken(models.Model):
    """DPO (Dynamic Partial Ownership) Token representing fractionalized NFT ownership"""
    original_nft = models.ForeignKey(NFTVault, on_delete=models.CASCADE, related_name='dpo_tokens')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # 0.01 to 100.00
    purchase_price = models.DecimalField(max_digits=20, decimal_places=8)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    is_for_sale = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DPO {self.ownership_percentage}% of {self.original_nft}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT_NFT', 'NFT Deposit'),
        ('WITHDRAW_NFT', 'NFT Withdrawal'),
        ('LOAN_CREATE', 'Loan Created'),
        ('LOAN_REPAY', 'Loan Repayment'),
        ('YIELD_RECEIVED', 'Yield Received'),
        ('PARTIAL_LIQUIDATION', 'Partial Liquidation'),
        ('FULL_LIQUIDATION', 'Full Liquidation'),
        ('FAUCET_CLAIM', 'Faucet Claim'),
        ('DPO_PURCHASE', 'DPO Token Purchase'),
        ('DPO_SALE', 'DPO Token Sale'),
        ('DPO_CREATED', 'DPO Token Created'),
        ('SWAP_COLLATERAL', 'Collateral Swap'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    related_nft = models.ForeignKey(NFTVault, on_delete=models.SET_NULL, null=True, blank=True)
    related_loan = models.ForeignKey(Loan, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.user.username} - {self.created_at}"

class FaucetClaim(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    ip_address = models.GenericIPAddressField()
    claimed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Faucet claim: {self.user.username} - {self.amount} vBTC"

class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"