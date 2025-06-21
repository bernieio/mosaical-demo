from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from .models import Loan, YieldRecord, Transaction, UserProfile

class InterestCalculator:
    """Utility class for calculating interest and yields"""

    @staticmethod
    def calculate_compound_interest(principal, rate, time_months):
        """Calculate compound interest for loans"""
        rate_decimal = rate / 100
        monthly_rate = rate_decimal / 12
        amount = principal * (1 + monthly_rate) ** time_months
        return amount - principal

    @staticmethod
    def update_loan_interest(loan):
        """Update interest for a specific loan"""
        now = timezone.now()
        time_diff = now - loan.last_interest_update
        months_passed = time_diff.days / 30.44  # Average days in a month

        if months_passed >= 0.033:  # Update if more than 1 day passed (1/30 month)
            interest = InterestCalculator.calculate_compound_interest(
                loan.current_debt, 
                loan.interest_rate, 
                months_passed
            )

            loan.current_debt += interest
            loan.ltv_ratio = (loan.current_debt / loan.nft_collateral.estimated_value) * 100
            loan.last_interest_update = now
            loan.save()

            # Record transaction
            Transaction.objects.create(
                user=loan.borrower,
                transaction_type='LOAN_REPAY',  # Negative amount for interest
                amount=-interest,
                related_loan=loan,
                description=f'Interest accrued: {interest:.8f} vBTC for loan #{loan.id}'
            )

            return interest
        return Decimal('0')

    @staticmethod
    def update_all_loans():
        """Update interest for all active loans"""
        from .models import Loan
        active_loans = Loan.objects.filter(status='ACTIVE')
        total_interest = Decimal('0')

        for loan in active_loans:
            interest = InterestCalculator.update_loan_interest(loan)
            total_interest += interest

        return total_interest

class YieldCalculator:
    """Utility class for calculating NFT yields"""

    @staticmethod
    def calculate_nft_yield(nft):
        """Calculate yield for a specific NFT"""
        base_rate = nft.collection.base_yield_rate / 100  # Convert to decimal
        utility_bonus = (nft.utility_score - 50) / 1000  # Utility score bonus/penalty

        # Calculate monthly yield
        monthly_yield_rate = base_rate + utility_bonus
        daily_yield_rate = monthly_yield_rate / 30.44

        # Calculate yield based on NFT value and ownership percentage
        daily_yield = (nft.estimated_value * daily_yield_rate * nft.ownership_percentage) / 100

        return max(daily_yield, Decimal('0'))  # Ensure non-negative

    @staticmethod
    def process_nft_yield(nft):
        """Process daily yield for an NFT"""
        now = timezone.now()
        last_yield = nft.last_yield_date or nft.deposit_date

        days_passed = (now - last_yield).days

        if days_passed >= 1:  # Process if at least 1 day passed
            daily_yield = YieldCalculator.calculate_nft_yield(nft)
            total_yield = daily_yield * days_passed

            if total_yield > 0:
                # Create yield record
                yield_record = YieldRecord.objects.create(
                    nft=nft,
                    amount=total_yield
                )

                # Check if NFT is collateralized and has active loan
                if nft.status == 'COLLATERALIZED':
                    try:
                        active_loan = Loan.objects.get(nft_collateral=nft, status='ACTIVE')

                        # Apply yield to loan repayment
                        if active_loan.current_debt > 0:
                            repayment = min(total_yield, active_loan.current_debt)
                            active_loan.current_debt -= repayment
                            active_loan.ltv_ratio = (active_loan.current_debt / nft.estimated_value) * 100
                            active_loan.save()

                            yield_record.applied_to_loan = active_loan
                            yield_record.save()

                            # Record transaction
                            Transaction.objects.create(
                                user=nft.owner,
                                transaction_type='YIELD_RECEIVED',
                                amount=repayment,
                                related_nft=nft,
                                related_loan=active_loan,
                                description=f'Yield {repayment:.8f} vBTC applied to loan #{active_loan.id}'
                            )

                            # If loan is fully repaid
                            if active_loan.current_debt <= Decimal('0.00000001'):
                                active_loan.status = 'REPAID'
                                active_loan.current_debt = Decimal('0')
                                active_loan.save()

                                nft.status = 'DEPOSITED'
                                nft.save()

                                Transaction.objects.create(
                                    user=nft.owner,
                                    transaction_type='LOAN_REPAY',
                                    amount=Decimal('0'),
                                    related_nft=nft,
                                    related_loan=active_loan,
                                    description=f'Loan #{active_loan.id} fully repaid through yield'
                                )

                            # Any remaining yield goes to user
                            remaining_yield = total_yield - repayment
                            if remaining_yield > 0:
                                profile = UserProfile.objects.get(user=nft.owner)
                                profile.add_balance(remaining_yield)
                                profile.save()

                                Transaction.objects.create(
                                    user=nft.owner,
                                    transaction_type='YIELD_RECEIVED',
                                    amount=remaining_yield,
                                    related_nft=nft,
                                    description=f'Excess yield {remaining_yield:.8f} {profile.get_currency_symbol()} to balance'
                                )
                        else:
                            # No debt, yield goes directly to user
                            profile = UserProfile.objects.get(user=nft.owner)
                            profile.add_balance(total_yield)
                            profile.save()

                            Transaction.objects.create(
                                user=nft.owner,
                                transaction_type='YIELD_RECEIVED',
                                amount=total_yield,
                                related_nft=nft,
                                description=f'Yield {total_yield:.8f} {profile.get_currency_symbol()} from {nft.collection.name} #{nft.token_id}'
                            )
                    except Loan.DoesNotExist:
                        # NFT is deposited but no active loan, yield goes to user
                        profile = UserProfile.objects.get(user=nft.owner)
                        profile.add_balance(total_yield)
                        profile.save()

                        Transaction.objects.create(
                            user=nft.owner,
                            transaction_type='YIELD_RECEIVED',
                            amount=total_yield,
                            related_nft=nft,
                            description=f'Yield {total_yield:.8f} {profile.get_currency_symbol()} from {nft.collection.name} #{nft.token_id}'
                        )
                else:
                    # NFT is deposited, yield goes to user
                    profile = UserProfile.objects.get(user=nft.owner)
                    profile.add_balance(total_yield)
                    profile.save()

                    Transaction.objects.create(
                        user=nft.owner,
                        transaction_type='YIELD_RECEIVED',
                        amount=total_yield,
                        related_nft=nft,
                        description=f'Yield {total_yield:.8f} {profile.get_currency_symbol()} from {nft.collection.name} #{nft.token_id}'
                    )

                # Update last yield date
                nft.last_yield_date = now
                nft.save()

                return total_yield

        return Decimal('0')

    @staticmethod
    def process_all_yields():
        """Process yields for all deposited NFTs"""
        from .models import NFTVault
        active_nfts = NFTVault.objects.exclude(status__in=['WITHDRAWN', 'LIQUIDATED'])
        total_yield = Decimal('0')

        for nft in active_nfts:
            yield_amount = YieldCalculator.process_nft_yield(nft)
            total_yield += yield_amount

        return total_yield

class LiquidationEngine:
    """Utility class for handling loan liquidations"""

    @staticmethod
    def check_liquidation_risk(loan):
        """Check if a loan is at risk of liquidation"""
        # Update interest first
        InterestCalculator.update_loan_interest(loan)

        # Calculate current LTV
        current_ltv = (loan.current_debt / loan.nft_collateral.estimated_value) * 100
        max_ltv = loan.nft_collateral.collection.max_ltv_ratio

        # Risk levels:
        # - Safe: LTV < 80% of max
        # - Warning: 80% <= LTV < 95% of max  
        # - Danger: 95% <= LTV < 100% of max
        # - Liquidation: LTV >= 100% of max

        if current_ltv >= max_ltv:
            return 'LIQUIDATION'
        elif current_ltv >= max_ltv * 0.95:
            return 'DANGER'
        elif current_ltv >= max_ltv * 0.80:
            return 'WARNING'
        else:
            return 'SAFE'

    @staticmethod
    def liquidate_loan(loan, liquidation_percentage=100):
        """Liquidate a loan (partial or full)"""
        if liquidation_percentage < 1 or liquidation_percentage > 100:
            raise ValueError("Liquidation percentage must be between 1 and 100")

        nft = loan.nft_collateral
        liquidation_amount = (loan.current_debt * liquidation_percentage) / 100
        nft_portion = (nft.ownership_percentage * liquidation_percentage) / 100

        with transaction.atomic():
            if liquidation_percentage == 100:
                # Full liquidation
                loan.status = 'LIQUIDATED'
                loan.current_debt = Decimal('0')
                loan.save()

                nft.status = 'LIQUIDATED'
                nft.ownership_percentage = Decimal('0')
                nft.save()

                Transaction.objects.create(
                    user=loan.borrower,
                    transaction_type='FULL_LIQUIDATION',
                    amount=liquidation_amount,
                    related_nft=nft,
                    related_loan=loan,
                    description=f'Full liquidation of loan #{loan.id} - {liquidation_amount:.8f} vBTC debt cleared'
                )
            else:
                # Partial liquidation
                loan.current_debt -= liquidation_amount
                loan.ltv_ratio = (loan.current_debt / nft.estimated_value) * 100
                loan.save()

                nft.status = 'PARTIAL_LIQUIDATED'
                nft.ownership_percentage -= nft_portion
                nft.save()

                # Create DPO token for liquidated portion
                from .models import DPOToken
                DPOToken.objects.create(
                    original_nft=nft,
                    owner=loan.borrower,  # Initially owned by original owner
                    ownership_percentage=nft_portion,
                    purchase_price=liquidation_amount
                )

                Transaction.objects.create(
                    user=loan.borrower,
                    transaction_type='PARTIAL_LIQUIDATION',
                    amount=liquidation_amount,
                    related_nft=nft,
                    related_loan=loan,
                    description=f'Partial liquidation ({liquidation_percentage}%) of loan #{loan.id} - {liquidation_amount:.8f} vBTC debt cleared'
                )

        return liquidation_amount

    @staticmethod
    def check_all_liquidations():
        """Check all active loans for liquidation risk"""
        from .models import Loan
        active_loans = Loan.objects.filter(status='ACTIVE')
        liquidations = []

        for loan in active_loans:
            risk_level = LiquidationEngine.check_liquidation_risk(loan)
            if risk_level == 'LIQUIDATION':
                # Auto-liquidate risky loans
                amount = LiquidationEngine.liquidate_loan(loan, 100)
                liquidations.append({
                    'loan': loan,
                    'amount': amount,
                    'type': 'FULL'
                })

        return liquidations