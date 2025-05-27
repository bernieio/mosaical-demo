
from django.core.management.base import BaseCommand
from django.utils import timezone
from mosaical_platform.valuation_oracle import ValuationOracle

class Command(BaseCommand):
    help = 'Update NFT valuations using the dynamic oracle'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write('=== DRY RUN MODE ===')
        
        start_time = timezone.now()
        updated_count = ValuationOracle.update_all_valuations() if not dry_run else 0
        end_time = timezone.now()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {updated_count} NFT valuations in {(end_time - start_time).seconds} seconds'
            )
        )
