
from django.core.management.base import BaseCommand
from django.utils import timezone
from mosaical_platform.ai_models import nft_predictor
from mosaical_platform.models import NFTVault
import numpy as np

class Command(BaseCommand):
    help = 'Train ensemble AI models (Random Forest, Gradient Boosting, XGBoost)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--samples',
            type=int,
            default=200,
            help='Number of training samples to generate',
        )

    def handle(self, *args, **options):
        samples = options['samples']
        
        self.stdout.write('🤖 Starting Ensemble Model Training...')
        self.stdout.write('📊 Models: Random Forest + Gradient Boosting + XGBoost')
        
        # Train the models
        success = nft_predictor.train_models()
        
        if success:
            # Test predictions on a few NFTs
            test_nfts = NFTVault.objects.exclude(status='WITHDRAWN')[:5]
            
            if test_nfts.exists():
                self.stdout.write('\n🔮 Testing predictions:')
                for nft in test_nfts:
                    try:
                        predicted_price = nft_predictor.predict_price(nft)
                        current_price = nft.estimated_value
                        change = float((predicted_price - current_price) / current_price * 100)
                        
                        self.stdout.write(
                            f'   NFT #{nft.id}: {current_price:.4f} → {predicted_price:.4f} vBTC ({change:+.1f}%)'
                        )
                    except Exception as e:
                        self.stdout.write(f'   ⚠️ Error predicting NFT #{nft.id}: {e}')
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Ensemble models trained successfully!'))
            self.stdout.write('📈 Available models:')
            self.stdout.write('   ✅ Random Forest Regressor')
            self.stdout.write('   ✅ Gradient Boosting Regressor')
            if nft_predictor.xgboost is not None:
                self.stdout.write('   ✅ XGBoost Regressor')
            else:
                self.stdout.write('   ⚠️ XGBoost not available')
            
            self.stdout.write('\n🌐 Models are now integrated and ready for web predictions!')
            
        else:
            self.stdout.write(self.style.ERROR('❌ Model training failed!'))
