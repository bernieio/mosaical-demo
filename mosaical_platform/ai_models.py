
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_percentage_error
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import json
import math
from .models import NFTVault, NFTCollection, Transaction, Loan, DPOToken
from django.db.models import Avg, Sum, Count, Q

class LSTMModel(nn.Module):
    """LSTM Model for NFT Price Prediction"""
    
    def __init__(self, input_size=10, hidden_size=64, num_layers=2, output_size=1):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc1 = nn.Linear(hidden_size, 32)
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(32, output_size)
        
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc1(out[:, -1, :])
        out = F.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        return out

class TransformerModel(nn.Module):
    """Transformer Model for NFT Price Prediction"""
    
    def __init__(self, input_size=15, d_model=128, nhead=8, num_layers=4, output_size=1):
        super(TransformerModel, self).__init__()
        self.d_model = d_model
        self.input_projection = nn.Linear(input_size, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead,
            dim_feedforward=512,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.fc1 = nn.Linear(d_model, 64)
        self.dropout = nn.Dropout(0.1)
        self.fc2 = nn.Linear(64, output_size)
        
    def forward(self, x):
        x = self.input_projection(x)
        x = self.transformer(x)
        x = x.mean(dim=1)  # Global average pooling
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x

class NFTPricePredictor:
    """Main NFT Price Prediction Engine"""
    
    def __init__(self):
        self.lstm_model = None
        self.transformer_model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        
        # Ensemble weights (optimized per NFT category)
        self.ensemble_weights = {
            'PFP': {'alpha': 0.25, 'beta': 0.6, 'gamma': 0.15},
            'Art': {'alpha': 0.2, 'beta': 0.7, 'gamma': 0.1},
            'Gaming': {'alpha': 0.15, 'beta': 0.65, 'gamma': 0.2},
            'Utility': {'alpha': 0.2, 'beta': 0.6, 'gamma': 0.2},
            'Default': {'alpha': 0.2, 'beta': 0.65, 'gamma': 0.15}
        }
        
    def extract_time_features(self, nft):
        """Extract time-series features for LSTM"""
        # Get price history (simulated - in real app would be from DB)
        features = []
        
        # Price history (30 days)
        base_price = float(nft.estimated_value)
        price_history = self._generate_price_history(base_price, 30)
        features.extend(price_history)
        
        # Volume history
        volume_history = self._get_volume_history(nft, 30)
        features.extend(volume_history)
        
        # Floor price history
        floor_history = self._get_floor_price_history(nft.collection, 30)
        features.extend(floor_history)
        
        # Volatility measures
        volatility_7d = self._calculate_volatility(price_history[-7:])
        volatility_30d = self._calculate_volatility(price_history)
        features.extend([volatility_7d, volatility_30d])
        
        # Market trend
        market_trend = self._get_market_trend()
        features.append(market_trend)
        
        return np.array(features)
    
    def extract_metadata_features(self, nft):
        """Extract metadata features for Transformer"""
        features = []
        
        # Artist features
        artist_features = self._get_artist_features(nft)
        features.extend(artist_features)
        
        # Category features  
        category_features = self._get_category_features(nft)
        features.extend(category_features)
        
        # DeFi features
        defi_features = self._get_defi_features(nft)
        features.extend(defi_features)
        
        # Metadata features
        meta_features = self._get_metadata_features(nft)
        features.extend(meta_features)
        
        return np.array(features)
    
    def _generate_price_history(self, base_price, days):
        """Generate realistic price history"""
        prices = []
        current_price = base_price
        
        for i in range(days):
            # Add realistic price movement
            change = np.random.normal(0, 0.05)  # 5% daily volatility
            current_price *= (1 + change)
            prices.append(current_price)
            
        return prices[-10:]  # Return last 10 days for LSTM
    
    def _get_volume_history(self, nft, days):
        """Get trading volume history"""
        # Simulate volume based on collection activity
        base_volume = 10
        volumes = []
        
        for i in range(min(days, 10)):
            volume = base_volume * np.random.uniform(0.5, 2.0)
            volumes.append(volume)
            
        return volumes
    
    def _get_floor_price_history(self, collection, days):
        """Get floor price history for collection"""
        # Simulate floor price trend
        base_floor = 1.0
        floors = []
        
        for i in range(min(days, 10)):
            floor = base_floor * np.random.uniform(0.8, 1.2)
            floors.append(floor)
            
        return floors
    
    def _calculate_volatility(self, prices):
        """Calculate price volatility"""
        if len(prices) < 2:
            return 0.0
            
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
            
        return float(np.std(returns)) if returns else 0.0
    
    def _get_market_trend(self):
        """Get overall market trend"""
        # Simulate market sentiment
        return np.random.normal(0, 0.1)  # ±10% market bias
    
    def _get_artist_features(self, nft):
        """Extract artist-related features"""
        # In real implementation, would query artist data
        return [
            2.5,    # artist_avg_price (normalized)
            100.0,  # artist_total_volume (normalized)
            0.15,   # artist_growth_rate
            7.5,    # artist_followers (0-10 scale)
            3,      # artist_previous_collections
            0.8,    # artist_success_ratio
            12      # artist_active_time (months)
        ]
    
    def _get_category_features(self, nft):
        """Extract category-related features"""
        category_mapping = {
            'CryptoKitties': 'PFP',
            'Bored Ape Yacht Club': 'PFP', 
            'Gods Unchained Cards': 'Gaming',
            'Axie Infinity': 'Gaming',
            'Sandbox Land': 'Metaverse'
        }
        
        category = category_mapping.get(nft.collection.name, 'Art')
        
        # Category performance metrics
        performance_map = {
            'PFP': 0.1, 'Art': 0.05, 'Gaming': 0.2, 'Metaverse': 0.15, 'Utility': 0.08
        }
        
        return [
            performance_map.get(category, 0.1),  # category_avg_performance
            7.0,  # category_liquidity
            1000.0,  # category_market_cap (normalized)
            0.12,  # category_growth
            float(nft.utility_score) / 10.0,  # utility_score (normalized)
            0.7,   # uniqueness_score
            8.0 if category == 'Gaming' else 5.0  # game_popularity_factor
        ]
    
    def _get_defi_features(self, nft):
        """Extract DeFi-related features"""
        # Get actual DeFi metrics from database
        ltv_ratio = float(nft.collection.max_ltv_ratio) / 100.0
        
        # Check if NFT has loan history
        has_loans = Loan.objects.filter(nft_collateral=nft).exists()
        
        return [
            ltv_ratio,  # ltv_ratio
            0.8 if has_loans else 0.2,  # loan_history (normalized)
            0.05,  # avg_interest_rate
            0.02,  # liquidation_frequency
            float(nft.estimated_value),  # collateral_value
            30.0,  # avg_loan_duration (days)
            500.0  # protocol_tvl (normalized)
        ]
    
    def _get_metadata_features(self, nft):
        """Extract metadata features"""
        # Calculate rarity score based on utility
        rarity_score = float(nft.utility_score) * 10.0
        rarity_percentile = min(float(nft.utility_score) * 2.0, 100.0)
        
        # Age in days
        age_days = (timezone.now() - nft.deposit_date).days
        
        return [
            rarity_score,     # rarity_score
            rarity_percentile, # rarity_percentile  
            5.0,              # trait_count
            rarity_percentile, # trait_rarity
            1.0,              # collection_rank (normalized)
            min(age_days, 365) / 365.0  # age_factor (normalized)
        ]
    
    def predict_price(self, nft):
        """Main prediction function"""
        try:
            # Extract features
            time_features = self.extract_time_features(nft)
            meta_features = self.extract_metadata_features(nft)
            
            # Get historical average
            historical_avg = float(nft.estimated_value)
            
            # LSTM prediction (simplified)
            lstm_pred = self._lstm_predict(time_features, historical_avg)
            
            # Transformer prediction (simplified)
            transformer_pred = self._transformer_predict(meta_features, historical_avg)
            
            # Get ensemble weights for NFT category
            category = self._get_nft_category(nft)
            weights = self.ensemble_weights.get(category, self.ensemble_weights['Default'])
            
            # Ensemble prediction
            final_pred = (
                weights['alpha'] * lstm_pred +
                weights['beta'] * transformer_pred + 
                weights['gamma'] * historical_avg
            )
            
            # Apply market adjustments
            adjusted_pred = self._apply_market_adjustments(nft, final_pred)
            
            # Ensure minimum price (80% of floor price)
            min_price = historical_avg * 0.8
            final_price = max(adjusted_pred, min_price)
            
            return Decimal(str(round(final_price, 8)))
            
        except Exception as e:
            print(f"Prediction error for NFT {nft.id}: {e}")
            return nft.estimated_value
    
    def _lstm_predict(self, features, base_price):
        """Simplified LSTM prediction"""
        # Simulate LSTM prediction with trend analysis
        trend = np.mean(features[-5:]) - np.mean(features[:5]) if len(features) >= 10 else 0
        prediction = base_price * (1 + trend * 0.1)
        return prediction
    
    def _transformer_predict(self, features, base_price):
        """Simplified Transformer prediction"""
        # Simulate Transformer prediction with feature importance
        feature_weights = [0.15, 0.12, 0.10, 0.08, 0.08, 0.07, 0.06, 0.05, 0.05, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04]
        
        if len(features) >= len(feature_weights):
            weighted_score = sum(f * w for f, w in zip(features[:len(feature_weights)], feature_weights))
            prediction = base_price * (1 + weighted_score * 0.2)
        else:
            prediction = base_price
            
        return prediction
    
    def _get_nft_category(self, nft):
        """Determine NFT category"""
        name = nft.collection.name.lower()
        if 'ape' in name or 'punk' in name or 'kitty' in name:
            return 'PFP'
        elif 'game' in name or 'axie' in name or 'gods' in name:
            return 'Gaming'
        elif 'sandbox' in name or 'land' in name:
            return 'Metaverse'
        else:
            return 'Art'
    
    def _apply_market_adjustments(self, nft, predicted_price):
        """Apply market-based adjustments"""
        # Liquidity adjustment
        liquidity_score = self._calculate_liquidity_score(nft)
        liquidity_discount = max(0, (2.0 - liquidity_score) * 0.05)  # 0-10% discount
        
        # Market correlation adjustment
        market_correlation = 0.6  # Assume moderate correlation
        market_trend = self._get_market_trend()
        market_adjustment = market_correlation * market_trend
        
        # Risk adjustment
        risk_score = self._calculate_risk_score(nft)
        risk_discount = risk_score * 0.15  # Up to 15% risk discount
        
        # Apply adjustments
        adjusted_price = predicted_price * (1 - liquidity_discount) * (1 + market_adjustment) * (1 - risk_discount)
        
        return adjusted_price
    
    def _calculate_liquidity_score(self, nft):
        """Calculate liquidity score (0-10)"""
        # Based on recent transaction volume and frequency
        recent_transactions = Transaction.objects.filter(
            related_nft__collection=nft.collection,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Normalize to 0-10 scale
        liquidity_score = min(recent_transactions / 10.0, 10.0)
        return liquidity_score
    
    def _calculate_risk_score(self, nft):
        """Calculate risk score (0-1)"""
        risk_factors = []
        
        # Age factor (newer = riskier)
        age_days = (timezone.now() - nft.deposit_date).days
        age_risk = max(0, (90 - age_days) / 90.0) * 0.3
        risk_factors.append(age_risk)
        
        # Loan status risk
        if nft.status == 'COLLATERALIZED':
            risk_factors.append(0.2)
        
        # Utility score risk (lower utility = higher risk)
        utility_risk = (100 - float(nft.utility_score)) / 200.0
        risk_factors.append(utility_risk)
        
        return min(sum(risk_factors), 1.0)
    
    def calculate_confidence_interval(self, nft, predicted_price):
        """Calculate prediction confidence interval"""
        base_volatility = self._calculate_volatility([float(predicted_price)] * 10)
        category_volatility = {
            'PFP': 0.12, 'Art': 0.16, 'Gaming': 0.20, 'Metaverse': 0.18, 'Utility': 0.22
        }
        
        category = self._get_nft_category(nft)
        volatility = category_volatility.get(category, 0.15)
        
        confidence_95 = predicted_price * volatility * 1.96
        
        return {
            'lower_bound': max(predicted_price - confidence_95, predicted_price * 0.5),
            'upper_bound': predicted_price + confidence_95,
            'confidence_level': 0.95
        }
    
    def detect_anomalies(self, nft, predicted_price):
        """Detect price anomalies"""
        current_price = nft.estimated_value
        price_change = abs(float(predicted_price) - float(current_price)) / float(current_price)
        
        anomalies = []
        
        if price_change > 0.3:  # >30% change
            severity = 'HIGH' if price_change > 0.5 else 'MEDIUM'
            direction = 'INCREASE' if predicted_price > current_price else 'DECREASE'
            
            anomalies.append({
                'type': f'PRICE_{direction}',
                'severity': severity,
                'change_percentage': price_change * 100,
                'message': f'Predicted {direction.lower()} of {price_change*100:.1f}%'
            })
        
        return anomalies

# Global predictor instance
nft_predictor = NFTPricePredictor()
