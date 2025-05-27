
from django.core.management.base import BaseCommand
from django.utils import timezone
from mosaical_platform.utils import YieldCalculator, InterestCalculator, LiquidationEngine

class Command(BaseCommand):
    help = 'Process NFT yields and update loan interests'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        self.stdout.write('Starting yield and interest processing...')
        
        # Process yields
        if not dry_run:
            total_yield = YieldCalculator.process_all_yields()
            self.stdout.write(
                self.style.SUCCESS(f'Processed yields: {total_yield:.8f} vBTC total')
            )
        
        # Update loan interests
        if not dry_run:
            total_interest = InterestCalculator.update_all_loans()
            self.stdout.write(
                self.style.SUCCESS(f'Updated loan interests: {total_interest:.8f} vBTC total')
            )
        
        # Check liquidations
        liquidations = LiquidationEngine.check_all_liquidations()
        if liquidations:
            for liq in liquidations:
                self.stdout.write(
                    self.style.WARNING(
                        f'Liquidated loan #{liq["loan"].id}: {liq["amount"]:.8f} vBTC ({liq["type"]})'
                    )
                )
        else:
            self.stdout.write('No liquidations required')
        
        self.stdout.write(
            self.style.SUCCESS(f'Processing completed at {timezone.now()}')
        )
