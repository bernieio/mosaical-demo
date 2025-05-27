
from decimal import Decimal
import random
from django.utils import timezone
from datetime import timedelta
from .models import NFTVault, NFTCollection

class ValuationOracle:
    """Dynamic NFT valuation based on market conditions"""
    
    @staticmethod
    def get_market_multiplier(collection):
        """Get market multiplier based on collection performance"""
        # Simulate market conditions (in real system, would fetch from APIs)
        base_multipliers = {
            'CryptoKitties': Decimal('0.95'),  # Slightly bearish
            'Axie Infinity': Decimal('1.10'),  # Bullish
            'Gods Unchained Cards': Decimal('1.05'),  # Moderately bullish
            'Bored Ape Yacht Club': Decimal('0.90'),  # Bearish
            'Sandbox Land': Decimal('1.15'),  # Very bullish
        }
        
        base = base_multipliers.get(collection.name, Decimal('1.0'))
        
        # Add random volatility ±5%
        volatility = Decimal(str(random.uniform(-0.05, 0.05)))
        return max(base + volatility, Decimal('0.5'))  # Minimum 0.5x multiplier
    
    @staticmethod
    def calculate_dynamic_value(nft):
        """Calculate dynamic value based on multiple factors"""
        base_value = nft.estimated_value
        
        # Market multiplier
        market_multiplier = ValuationOracle.get_market_multiplier(nft.collection)
        
        # Utility score impact (±20% based on utility)
        utility_multiplier = Decimal('0.8') + (nft.utility_score / Decimal('250'))
        
        # Time-based appreciation (0.1% per day up to 10%)
        days_held = (timezone.now() - nft.deposit_date).days
        time_multiplier = Decimal('1.0') + min(days_held * Decimal('0.001'), Decimal('0.1'))
        
        # Loan status penalty (5% if collateralized)
        status_multiplier = Decimal('0.95') if nft.status == 'COLLATERALIZED' else Decimal('1.0')
        
        new_value = base_value * market_multiplier * utility_multiplier * time_multiplier * status_multiplier
        
        return max(new_value, base_value * Decimal('0.5'))  # Never less than 50% of original
    
    @staticmethod
    def update_all_valuations():
        """Update all NFT valuations"""
        updated_count = 0
        
        for nft in NFTVault.objects.exclude(status='WITHDRAWN'):
            old_value = nft.estimated_value
            new_value = ValuationOracle.calculate_dynamic_value(nft)
            
            if abs(new_value - old_value) / old_value > Decimal('0.01'):  # Update if >1% change
                nft.estimated_value = new_value
                nft.save()
                updated_count += 1
                
                # Update related loan LTV if exists
                if hasattr(nft, 'loan_set'):
                    for loan in nft.loan_set.filter(status='ACTIVE'):
                        loan.ltv_ratio = (loan.current_debt / new_value) * 100
                        loan.save()
        
        return updated_count
