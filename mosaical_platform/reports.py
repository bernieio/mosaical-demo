
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import *

class FinancialReports:
    """Generate detailed financial reports"""
    
    @staticmethod
    def generate_platform_summary(days=30):
        """Generate platform-wide financial summary"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Loan metrics
        total_loans = Loan.objects.filter(created_at__gte=start_date)
        active_loans = total_loans.filter(status='ACTIVE')
        
        total_loan_volume = total_loans.aggregate(
            sum=Sum('principal_amount')
        )['sum'] or Decimal('0')
        
        total_outstanding = active_loans.aggregate(
            sum=Sum('current_debt')
        )['sum'] or Decimal('0')
        
        # NFT metrics
        total_nfts = NFTVault.objects.filter(deposit_date__gte=start_date)
        total_nft_value = total_nfts.aggregate(
            sum=Sum('estimated_value')
        )['sum'] or Decimal('0')
        
        # Transaction metrics
        transactions = Transaction.objects.filter(created_at__gte=start_date)
        yield_paid = transactions.filter(
            transaction_type='YIELD_RECEIVED'
        ).aggregate(sum=Sum('amount'))['sum'] or Decimal('0')
        
        # DPO metrics
        dpo_trades = transactions.filter(
            transaction_type__in=['DPO_PURCHASE', 'DPO_SALE']
        )
        dpo_volume = dpo_trades.aggregate(
            sum=Sum('amount')
        )['sum'] or Decimal('0')
        
        return {
            'period_days': days,
            'total_users': User.objects.filter(date_joined__gte=start_date).count(),
            'total_loans': total_loans.count(),
            'active_loans': active_loans.count(),
            'total_loan_volume': total_loan_volume,
            'total_outstanding_debt': total_outstanding,
            'total_nfts_deposited': total_nfts.count(),
            'total_nft_value': total_nft_value,
            'total_yield_distributed': yield_paid,
            'dpo_trading_volume': dpo_volume,
            'avg_loan_size': total_loan_volume / max(total_loans.count(), 1),
            'platform_utilization': (total_outstanding / max(total_nft_value, 1)) * 100,
        }
    
    @staticmethod
    def generate_user_report(user, days=30):
        """Generate individual user financial report"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # User's transactions
        transactions = Transaction.objects.filter(
            user=user,
            created_at__gte=start_date
        )
        
        # Loan history
        loans = Loan.objects.filter(
            borrower=user,
            created_at__gte=start_date
        )
        
        # NFT portfolio
        nfts = NFTVault.objects.filter(owner=user).exclude(status='WITHDRAWN')
        
        # Yield earned
        yield_earned = transactions.filter(
            transaction_type='YIELD_RECEIVED'
        ).aggregate(sum=Sum('amount'))['sum'] or Decimal('0')
        
        # Interest paid
        interest_paid = transactions.filter(
            transaction_type='LOAN_REPAY',
            amount__lt=0
        ).aggregate(sum=Sum('amount'))['sum'] or Decimal('0')
        
        return {
            'user': user.username,
            'period_days': days,
            'current_balance': user.userprofile.vbtc_balance,
            'total_loans': loans.count(),
            'active_loans': loans.filter(status='ACTIVE').count(),
            'total_borrowed': loans.aggregate(sum=Sum('principal_amount'))['sum'] or Decimal('0'),
            'current_debt': loans.filter(status='ACTIVE').aggregate(sum=Sum('current_debt'))['sum'] or Decimal('0'),
            'nfts_owned': nfts.count(),
            'portfolio_value': nfts.aggregate(sum=Sum('estimated_value'))['sum'] or Decimal('0'),
            'total_yield_earned': yield_earned,
            'total_interest_paid': abs(interest_paid),
            'net_profit': yield_earned + interest_paid,
        }
    
    @staticmethod
    def generate_collection_report():
        """Generate report by NFT collection"""
        collections = NFTCollection.objects.all()
        report = []
        
        for collection in collections:
            nfts = NFTVault.objects.filter(collection=collection).exclude(status='WITHDRAWN')
            loans = Loan.objects.filter(nft_collateral__collection=collection)
            
            total_value = nfts.aggregate(sum=Sum('estimated_value'))['sum'] or Decimal('0')
            total_loans = loans.aggregate(sum=Sum('principal_amount'))['sum'] or Decimal('0')
            
            report.append({
                'collection_name': collection.name,
                'game_name': collection.game_name,
                'total_nfts': nfts.count(),
                'total_value': total_value,
                'total_loans': total_loans,
                'utilization_rate': (total_loans / max(total_value, 1)) * 100,
                'avg_ltv': collection.max_ltv_ratio,
                'yield_rate': collection.base_yield_rate,
            })
        
        return sorted(report, key=lambda x: x['total_value'], reverse=True)
