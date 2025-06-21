from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from mosaical_platform.models import (
    UserProfile, NFTCollection, NFTVault, Loan, 
    SystemSettings, DPOToken
)
from decimal import Decimal
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Load sample data for Mosaical platform'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')

        # Create system settings
        SystemSettings.objects.get_or_create(
            key='FAUCET_SECRET_KEY',
            defaults={'value': 'MOSAICAL_DEVPROS_2025', 'description': 'Secret key for faucet access'}
        )

        # Create sample NFT collections
        collections_data = [
            {
                'name': 'CryptoKitties',
                'game_name': 'CryptoKitties',
                'max_ltv_ratio': Decimal('70.00'),
                'base_yield_rate': Decimal('2.50')
            },
            {
                'name': 'Axie Infinity',
                'game_name': 'Axie Infinity',
                'max_ltv_ratio': Decimal('80.00'),
                'base_yield_rate': Decimal('3.00')
            },
            {
                'name': 'Bored Ape Yacht Club',
                'game_name': 'BAYC',
                'max_ltv_ratio': Decimal('60.00'),
                'base_yield_rate': Decimal('1.80')
            },
            {
                'name': 'Sandbox Land',
                'game_name': 'The Sandbox',
                'max_ltv_ratio': Decimal('75.00'),
                'base_yield_rate': Decimal('2.20')
            },
            {
                'name': 'Gods Unchained Cards',
                'game_name': 'Gods Unchained',
                'max_ltv_ratio': Decimal('65.00'),
                'base_yield_rate': Decimal('4.00')
            }
        ]

        collections = []
        for data in collections_data:
            collection, created = NFTCollection.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            collections.append(collection)
            if created:
                self.stdout.write(f'Created collection: {collection.name}')

        # Create sample users with explicit password setting
        sample_users = [
            ('gamefi_player1', 'samplepass123'),
            ('nft_collector', 'samplepass123'),
            ('defi_trader', 'samplepass123'),
            ('crypto_whale', 'samplepass123'),
        ]

        users = []
        for username, password in sample_users:
            if User.objects.filter(username=username).exists():
                # Delete existing user to recreate with correct password
                User.objects.filter(username=username).delete()

            user = User.objects.create_user(
                username=username, 
                password=password,
                email=f'{username}@example.com'
            )
            UserProfile.objects.create(user=user, dpsv_balance=10.0)  # Start with some DPSV
            users.append(user)  # Add to users list
            self.stdout.write(f"Created user: {username} with password: {password}")

        # Create sample NFTs
        nft_names = [
            'Genesis Dragon', 'Mystic Phoenix', 'Shadow Wolf', 'Crystal Unicorn',
            'Fire Demon', 'Ice Queen', 'Thunder God', 'Earth Golem',
            'Wind Spirit', 'Water Nymph', 'Legendary Sword', 'Magic Shield',
            'Golden Armor', 'Silver Bow', 'Diamond Ring', 'Ruby Amulet'
        ]

        for i in range(20):
            if users:
                owner = random.choice(users)
                collection = random.choice(collections)

                nft, created = NFTVault.objects.get_or_create(
                    collection=collection,
                    token_id=str(1000 + i),
                    defaults={
                        'owner': owner,
                        'name': random.choice(nft_names),
                        'estimated_value': Decimal(str(random.uniform(10, 200))),
                        'utility_score': random.randint(30, 90),
                        'status': random.choice(['DEPOSITED', 'COLLATERALIZED'])
                    }
                )

                if created:
                    self.stdout.write(f'Created NFT: {nft.name} #{nft.token_id}')

                    # Create some loans for collateralized NFTs
                    if nft.status == 'COLLATERALIZED' and random.choice([True, False]):
                        max_loan = (nft.estimated_value * collection.max_ltv_ratio) / 100
                        loan_amount = Decimal(str(random.uniform(float(max_loan * Decimal('0.3')), float(max_loan * Decimal('0.8')))))

                        Loan.objects.create(
                            borrower=owner,
                            nft_collateral=nft,
                            principal_amount=loan_amount,
                            current_debt=loan_amount * Decimal('1.1'),  # Some interest accrued
                            ltv_ratio=(loan_amount / nft.estimated_value) * 100,
                            interest_rate=Decimal('5.00')
                        )
                        self.stdout.write(f'Created loan for NFT #{nft.token_id}')

        # Create some DPO tokens
        deposited_nfts = NFTVault.objects.filter(status='DEPOSITED')[:5]
        for nft in deposited_nfts:
            if random.choice([True, False]):
                DPOToken.objects.create(
                    original_nft=nft,
                    owner=nft.owner,
                    ownership_percentage=Decimal(str(random.uniform(10, 30))),
                    purchase_price=nft.estimated_value * Decimal('0.2'),
                    current_price=nft.estimated_value * Decimal(str(random.uniform(0.15, 0.25))),
                    is_for_sale=True
                )
                self.stdout.write(f'Created DPO token for NFT #{nft.token_id}')

        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))
        self.stdout.write(f'Collections: {NFTCollection.objects.count()}')
        self.stdout.write(f'Users: {User.objects.count()}')
        self.stdout.write(f'NFTs: {NFTVault.objects.count()}')
        self.stdout.write(f'Loans: {Loan.objects.count()}')
        self.stdout.write(f'DPO Tokens: {DPOToken.objects.count()}')