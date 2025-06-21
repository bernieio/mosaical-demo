
from django.contrib import admin
from .models import (
    UserProfile, NFTCollection, NFTVault, Loan, YieldRecord, 
    DPOToken, Transaction, FaucetClaim, SystemSettings
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'dpsv_balance', 'total_nfts', 'active_loans', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def total_nfts(self, obj):
        return obj.user.nftvault_set.exclude(status='WITHDRAWN').count()
    total_nfts.short_description = 'Total NFTs'
    
    def active_loans(self, obj):
        return obj.user.loan_set.filter(status='ACTIVE').count()
    active_loans.short_description = 'Active Loans'

@admin.register(NFTCollection)
class NFTCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'game_name', 'max_ltv_ratio', 'base_yield_rate', 'is_active']
    list_filter = ['is_active', 'game_name']
    search_fields = ['name', 'game_name']

@admin.register(NFTVault)
class NFTVaultAdmin(admin.ModelAdmin):
    list_display = ['token_id', 'collection', 'owner', 'estimated_value', 'status', 'ownership_percentage', 'has_loan', 'yield_potential']
    list_filter = ['status', 'collection', 'deposit_date']
    search_fields = ['token_id', 'name', 'owner__username']
    readonly_fields = ['deposit_date']
    
    def has_loan(self, obj):
        return obj.loan_set.filter(status='ACTIVE').exists()
    has_loan.boolean = True
    has_loan.short_description = 'Has Active Loan'
    
    def yield_potential(self, obj):
        from .utils import YieldCalculator
        return f"{YieldCalculator.calculate_nft_yield(obj):.6f} DPSV/day"
    yield_potential.short_description = 'Daily Yield'

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['id', 'borrower', 'nft_collateral', 'principal_amount', 'current_debt', 'ltv_ratio', 'status', 'risk_level', 'health_factor']
    list_filter = ['status', 'created_at']
    search_fields = ['borrower__username', 'nft_collateral__token_id']
    readonly_fields = ['created_at', 'last_interest_update']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['borrower', 'nft_collateral', 'principal_amount']
        return self.readonly_fields
    
    def risk_level(self, obj):
        from .utils import LiquidationEngine
        risk = LiquidationEngine.check_liquidation_risk(obj)
        colors = {
            'SAFE': 'green',
            'WARNING': 'orange', 
            'DANGER': 'red',
            'LIQUIDATION': 'darkred'
        }
        return f'<span style="color: {colors.get(risk, "black")}">{risk}</span>'
    risk_level.allow_tags = True
    risk_level.short_description = 'Risk Level'
    
    def health_factor(self, obj):
        return f"{obj.calculate_health_factor():.1f}%"
    health_factor.short_description = 'Health Factor'

@admin.register(YieldRecord)
class YieldRecordAdmin(admin.ModelAdmin):
    list_display = ['nft', 'amount', 'yield_date', 'applied_to_loan']
    list_filter = ['yield_date']
    search_fields = ['nft__token_id', 'nft__owner__username']
    readonly_fields = ['yield_date']

@admin.register(DPOToken)
class DPOTokenAdmin(admin.ModelAdmin):
    list_display = ['original_nft', 'owner', 'ownership_percentage', 'purchase_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['original_nft__token_id', 'owner__username']
    readonly_fields = ['created_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'related_nft', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']

@admin.register(FaucetClaim)
class FaucetClaimAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'ip_address', 'claimed_at']
    list_filter = ['claimed_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['claimed_at']

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['updated_at']
