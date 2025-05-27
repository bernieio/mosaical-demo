#!/usr/bin/env python3

from django.core.management.base import BaseCommand
from django.utils import timezone
from mosaical_platform.utils import YieldCalculator
from mosaical_platform.models import SystemSettings
from decimal import Decimal

class Command(BaseCommand):
    help = 'Process yields for all deposited NFTs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting yield processing at {timezone.now()}')
        )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        try:
            if not options['dry_run']:
                total_yield = YieldCalculator.process_all_yields()

                # Update last processing time
                last_processing, created = SystemSettings.objects.get_or_create(
                    key='last_yield_processing',
                    defaults={
                        'value': str(timezone.now()),
                        'description': 'Last time yields were processed'
                    }
                )
                if not created:
                    last_processing.value = str(timezone.now())
                    last_processing.save()

                # Run auto liquidation check after yield processing
                self.stdout.write('Running auto liquidation check...')
                from mosaical_platform.utils import LiquidationEngine
                liquidations = LiquidationEngine.check_all_liquidations()

                if liquidations:
                    for liq in liquidations:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Auto-liquidated loan #{liq["loan"].id}: {liq["amount"]:.8f} vBTC'
                            )
                        )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed yields. Total yield distributed: {total_yield} vBTC'
                    )
                )
            else:
                # Dry run - just show what would happen
                from mosaical_platform.models import NFTVault
                active_nfts = NFTVault.objects.exclude(status__in=['WITHDRAWN', 'LIQUIDATED'])

                self.stdout.write(f'Would process yields for {active_nfts.count()} NFTs:')
                for nft in active_nfts:
                    estimated_yield = YieldCalculator.calculate_yield(nft)
                    self.stdout.write(f'  - {nft}: {estimated_yield} vBTC')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing yields: {str(e)}')
            )
            raise

        self.stdout.write(
            self.style.SUCCESS(f'Yield processing completed at {timezone.now()}')
        )