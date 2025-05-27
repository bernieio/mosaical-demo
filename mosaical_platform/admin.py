
from django.contrib import admin
from .models import (
    UserProfile, NFTCollection, NFTVault, Loan, YieldRecord, 
    DPOToken, Transaction, FaucetClaim, SystemSettings
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'vbtc_balance', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(NFTCollection)
class NFTCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'game_name', 'max_ltv_ratio', 'base_yield_rate', 'is_active']
    list_filter = ['is_active', 'game_name']
    search_fields = ['name', 'game_name']

@admin.register(NFTVault)
class NFTVaultAdmin(admin.ModelAdmin):
    list_display = ['token_id', 'collection', 'owner', 'estimated_value', 'status', 'ownership_percentage']
    list_filter = ['status', 'collection', 'deposit_date']
    search_fields = ['token_id', 'name', 'owner__username']
    readonly_fields = ['deposit_date']

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['id', 'borrower', 'nft_collateral', 'principal_amount', 'current_debt', 'ltv_ratio', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['borrower__username', 'nft_collateral__token_id']
    readonly_fields = ['created_at', 'last_interest_update']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['borrower', 'nft_collateral', 'principal_amount']
        return self.readonly_fields

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
