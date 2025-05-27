
from django.core.management.base import BaseCommand
from django.db import transaction
from mosaical_platform.utils import LiquidationEngine, InterestCalculator
from mosaical_platform.models import Loan, Transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Run automatic liquidation check for risky loans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be liquidated without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual liquidations will occur'))
        
        # Update all loan interests first
        self.stdout.write('Updating interest for all active loans...')
        total_interest = InterestCalculator.update_all_loans()
        self.stdout.write(f'Total interest accrued: {total_interest:.8f} vBTC')
        
        # Check for liquidations
        self.stdout.write('Checking for loans requiring liquidation...')
        active_loans = Loan.objects.filter(status='ACTIVE')
        liquidated_count = 0
        total_liquidated_amount = Decimal('0')
        
        for loan in active_loans:
            risk_level = LiquidationEngine.check_liquidation_risk(loan)
            current_ltv = (loan.current_debt / loan.nft_collateral.estimated_value) * 100
            
            self.stdout.write(f'Loan #{loan.id}: LTV {current_ltv:.2f}% - Risk: {risk_level}')
            
            if risk_level == 'LIQUIDATION':
                if not dry_run:
                    try:
                        with transaction.atomic():
                            amount = LiquidationEngine.liquidate_loan(loan, 100)
                            liquidated_count += 1
                            total_liquidated_amount += amount
                            
                            self.stdout.write(
                                self.style.ERROR(
                                    f'LIQUIDATED: Loan #{loan.id} - {amount:.8f} vBTC debt cleared'
                                )
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to liquidate loan #{loan.id}: {str(e)}')
                        )
                else:
                    liquidated_count += 1
                    total_liquidated_amount += loan.current_debt
                    self.stdout.write(
                        self.style.WARNING(
                            f'WOULD LIQUIDATE: Loan #{loan.id} - {loan.current_debt:.8f} vBTC debt'
                        )
                    )
            elif risk_level == 'DANGER':
                self.stdout.write(
                    self.style.WARNING(f'HIGH RISK: Loan #{loan.id} near liquidation threshold')
                )
        
        if liquidated_count > 0:
            mode = "Would liquidate" if dry_run else "Liquidated"
            self.stdout.write(
                self.style.SUCCESS(
                    f'{mode} {liquidated_count} loans totaling {total_liquidated_amount:.8f} vBTC'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('No loans require liquidation'))
        
        self.stdout.write(self.style.SUCCESS('Auto liquidation check completed'))
