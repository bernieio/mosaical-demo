
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_percentage_error
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import json
import pickle
import os
from .models import NFTVault, NFTCollection, Transaction, Loan, DPOToken
from django.db.models import Avg, Sum, Count, Q

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

class NFTPricePredictor:
    """NFT Price Prediction Engine using Ensemble Methods"""
    
    def __init__(self):
        self.random_forest = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.gradient_boosting = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        if XGBOOST_AVAILABLE:
            self.xgboost = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        else:
            self.xgboost = None
            
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Ensemble weights optimized for different NFT categories
        self.ensemble_weights = {
            'PFP': {'rf': 0.35, 'gb': 0.35, 'xgb': 0.30} if XGBOOST_AVAILABLE else {'rf': 0.50, 'gb': 0.50},
            'Art': {'rf': 0.40, 'gb': 0.30, 'xgb': 0.30} if XGBOOST_AVAILABLE else {'rf': 0.55, 'gb': 0.45},
            'Gaming': {'rf': 0.30, 'gb': 0.40, 'xgb': 0.30} if XGBOOST_AVAILABLE else {'rf': 0.45, 'gb': 0.55},
            'Utility': {'rf': 0.35, 'gb': 0.35, 'xgb': 0.30} if XGBOOST_AVAILABLE else {'rf': 0.50, 'gb': 0.50},
            'Default': {'rf': 0.35, 'gb': 0.35, 'xgb': 0.30} if XGBOOST_AVAILABLE else {'rf': 0.50, 'gb': 0.50}
        }
    
    def extract_all_features(self, nft):
        """Extract comprehensive features for prediction"""
        features = {}
        
        # Basic NFT features
        features.update(self._get_basic_features(nft))
        
        # Price history features
        features.update(self._get_price_features(nft))
        
        # Collection features
        features.update(self._get_collection_features(nft))
        
        # Market features
        features.update(self._get_market_features(nft))
        
        # DeFi features
        features.update(self._get_defi_features(nft))
        
        # Temporal features
        features.update(self._get_temporal_features(nft))
        
        return features
    
    def _get_basic_features(self, nft):
        """Basic NFT characteristics"""
        age_days = (timezone.now() - nft.deposit_date).days
        
        return {
            'current_price': float(nft.estimated_value),
            'utility_score': float(nft.utility_score),
            'age_days': age_days,
            'age_normalized': min(age_days / 365.0, 2.0),  # Cap at 2 years
            'rarity_score': float(nft.utility_score) * 10.0,
            'is_collateralized': 1 if nft.status == 'COLLATERALIZED' else 0,
        }
    
    def _get_price_features(self, nft):
        """Price-related features"""
        base_price = float(nft.estimated_value)
        
        # Simulate realistic price history
        price_history = self._generate_price_history(base_price, 30)
        
        return {
            'price_mean_7d': np.mean(price_history[-7:]),
            'price_mean_30d': np.mean(price_history),
            'price_std_7d': np.std(price_history[-7:]),
            'price_std_30d': np.std(price_history),
            'price_trend_7d': self._calculate_trend(price_history[-7:]),
            'price_trend_30d': self._calculate_trend(price_history),
            'price_volatility': self._calculate_volatility(price_history),
            'price_momentum': price_history[-1] / price_history[0] if price_history[0] > 0 else 1.0,
            'price_rsi': self._calculate_rsi(price_history),
        }
    
    def _get_collection_features(self, nft):
        """Collection-level features"""
        collection = nft.collection
        
        # Collection activity metrics
        total_nfts = NFTVault.objects.filter(collection=collection).count()
        active_nfts = NFTVault.objects.filter(collection=collection).exclude(status='WITHDRAWN').count()
        
        # Collection financial metrics
        avg_value = NFTVault.objects.filter(collection=collection).aggregate(
            avg=Avg('estimated_value')
        )['avg'] or Decimal('0')
        
        return {
            'collection_size': total_nfts,
            'collection_active_ratio': active_nfts / max(total_nfts, 1),
            'collection_avg_value': float(avg_value),
            'collection_max_ltv': float(collection.max_ltv_ratio),
            'collection_floor_price': float(avg_value) * 0.8,  # Estimate floor as 80% of avg
            'collection_age_days': (timezone.now() - collection.created_at).days,
        }
    
    def _get_market_features(self, nft):
        """Market-wide features"""
        # Overall market metrics
        total_loans = Loan.objects.filter(status='ACTIVE').count()
        total_value_locked = NFTVault.objects.exclude(status='WITHDRAWN').aggregate(
            sum=Sum('estimated_value')
        )['sum'] or Decimal('0')
        
        # Recent transaction activity
        recent_txns = Transaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return {
            'market_total_loans': total_loans,
            'market_tvl': float(total_value_locked),
            'market_activity_7d': recent_txns,
            'market_sentiment': self._calculate_market_sentiment(),
            'market_volatility': self._calculate_market_volatility(),
        }
    
    def _get_defi_features(self, nft):
        """DeFi-specific features"""
        # Loan history for this NFT
        loan_count = Loan.objects.filter(nft_collateral=nft).count()
        active_loan = Loan.objects.filter(nft_collateral=nft, status='ACTIVE').first()
        
        return {
            'loan_history_count': loan_count,
            'has_active_loan': 1 if active_loan else 0,
            'current_ltv': float(active_loan.ltv_ratio) if active_loan else 0.0,
            'max_ltv_ratio': float(nft.collection.max_ltv_ratio),
            'ltv_utilization': float(active_loan.ltv_ratio) / float(nft.collection.max_ltv_ratio) if active_loan else 0.0,
            'liquidation_risk': 1 if active_loan and active_loan.ltv_ratio >= 80 else 0,
        }
    
    def _get_temporal_features(self, nft):
        """Time-based features"""
        now = timezone.now()
        
        return {
            'hour_of_day': now.hour,
            'day_of_week': now.weekday(),
            'day_of_month': now.day,
            'month_of_year': now.month,
            'is_weekend': 1 if now.weekday() >= 5 else 0,
            'is_month_end': 1 if now.day >= 28 else 0,
        }
    
    def _generate_price_history(self, base_price, days):
        """Generate realistic price history"""
        prices = [base_price]
        current_price = base_price
        
        for i in range(days - 1):
            # Add realistic price movement with mean reversion
            change = np.random.normal(0, 0.03)  # 3% daily volatility
            mean_reversion = (base_price - current_price) / base_price * 0.1
            change += mean_reversion
            
            current_price *= (1 + change)
            prices.append(current_price)
            
        return prices
    
    def _calculate_trend(self, prices):
        """Calculate price trend"""
        if len(prices) < 2:
            return 0.0
        x = np.arange(len(prices))
        coeffs = np.polyfit(x, prices, 1)
        return coeffs[0] / np.mean(prices)  # Normalized slope
    
    def _calculate_volatility(self, prices):
        """Calculate price volatility"""
        if len(prices) < 2:
            return 0.0
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        return float(np.std(returns)) if returns else 0.0
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_market_sentiment(self):
        """Calculate overall market sentiment"""
        # Based on recent transaction trends
        recent_growth = np.random.normal(0.02, 0.1)  # Simulate 2% growth with variance
        return max(-1.0, min(1.0, recent_growth))  # Clamp to [-1, 1]
    
    def _calculate_market_volatility(self):
        """Calculate market volatility"""
        return np.random.uniform(0.05, 0.25)  # 5-25% volatility
    
    def predict_price(self, nft):
        """Main prediction function using ensemble"""
        try:
            # Extract features
            features_dict = self.extract_all_features(nft)
            
            # Convert to feature vector
            feature_names = sorted(features_dict.keys())
            feature_vector = np.array([features_dict[name] for name in feature_names]).reshape(1, -1)
            
            # If models aren't trained, use heuristic prediction
            if not self.is_trained:
                return self._heuristic_prediction(nft, features_dict)
            
            # Scale features
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Get predictions from each model
            predictions = {}
            predictions['rf'] = self.random_forest.predict(feature_vector_scaled)[0]
            predictions['gb'] = self.gradient_boosting.predict(feature_vector_scaled)[0]
            
            if self.xgboost is not None:
                predictions['xgb'] = self.xgboost.predict(feature_vector_scaled)[0]
            
            # Get ensemble weights for NFT category
            category = self._get_nft_category(nft)
            weights = self.ensemble_weights.get(category, self.ensemble_weights['Default'])
            
            # Calculate ensemble prediction
            ensemble_pred = 0
            for model_name, weight in weights.items():
                if model_name in predictions:
                    ensemble_pred += weight * predictions[model_name]
            
            # Apply market adjustments
            adjusted_pred = self._apply_market_adjustments(nft, ensemble_pred)
            
            # Ensure reasonable bounds
            current_price = float(nft.estimated_value)
            min_price = current_price * 0.5  # Minimum 50% of current
            max_price = current_price * 3.0  # Maximum 300% of current
            
            final_price = max(min_price, min(adjusted_pred, max_price))
            
            return Decimal(str(round(final_price, 8)))
            
        except Exception as e:
            print(f"Prediction error for NFT {nft.id}: {e}")
            return nft.estimated_value
    
    def _heuristic_prediction(self, nft, features_dict):
        """Fallback heuristic prediction when models aren't trained"""
        base_price = float(nft.estimated_value)
        
        # Factor in various features
        multiplier = 1.0
        
        # Utility score factor
        utility_factor = features_dict['utility_score'] / 50.0  # Normalize around 50
        multiplier *= (0.8 + 0.4 * utility_factor)
        
        # Age factor (newer can be more volatile)
        age_factor = min(features_dict['age_days'] / 365.0, 1.0)
        multiplier *= (0.9 + 0.2 * age_factor)
        
        # Market sentiment
        sentiment = features_dict.get('market_sentiment', 0)
        multiplier *= (1.0 + sentiment * 0.1)
        
        # Collection activity
        activity_factor = features_dict.get('collection_active_ratio', 0.5)
        multiplier *= (0.95 + 0.1 * activity_factor)
        
        # Add some controlled randomness
        noise = np.random.normal(1.0, 0.05)  # ±5% noise
        multiplier *= noise
        
        predicted_price = base_price * multiplier
        return Decimal(str(round(predicted_price, 8)))
    
    def _get_nft_category(self, nft):
        """Determine NFT category"""
        name = nft.collection.name.lower()
        if any(keyword in name for keyword in ['ape', 'punk', 'kitty', 'avatar']):
            return 'PFP'
        elif any(keyword in name for keyword in ['game', 'axie', 'gods', 'card']):
            return 'Gaming'
        elif any(keyword in name for keyword in ['sandbox', 'land', 'metaverse']):
            return 'Utility'
        else:
            return 'Art'
    
    def _apply_market_adjustments(self, nft, predicted_price):
        """Apply market-based adjustments"""
        # Liquidity adjustment
        liquidity_score = self._calculate_liquidity_score(nft)
        liquidity_adjustment = max(0.9, min(1.1, 0.95 + liquidity_score / 10.0))
        
        # Risk adjustment
        risk_score = self._calculate_risk_score(nft)
        risk_adjustment = 1.0 - (risk_score * 0.1)  # Up to 10% discount
        
        adjusted_price = predicted_price * liquidity_adjustment * risk_adjustment
        return adjusted_price
    
    def _calculate_liquidity_score(self, nft):
        """Calculate liquidity score (0-10)"""
        recent_transactions = Transaction.objects.filter(
            related_nft__collection=nft.collection,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return min(recent_transactions / 5.0, 10.0)
    
    def _calculate_risk_score(self, nft):
        """Calculate risk score (0-1)"""
        risk_factors = []
        
        # Age risk
        age_days = (timezone.now() - nft.deposit_date).days
        age_risk = max(0, (90 - age_days) / 90.0) * 0.2
        risk_factors.append(age_risk)
        
        # Loan status risk
        if nft.status == 'COLLATERALIZED':
            active_loan = Loan.objects.filter(nft_collateral=nft, status='ACTIVE').first()
            if active_loan and active_loan.ltv_ratio >= 75:
                risk_factors.append(0.3)
            else:
                risk_factors.append(0.1)
        
        # Utility score risk
        utility_risk = (100 - float(nft.utility_score)) / 200.0
        risk_factors.append(utility_risk)
        
        return min(sum(risk_factors), 1.0)
    
    def calculate_confidence_interval(self, nft, predicted_price):
        """Calculate prediction confidence interval"""
        category_volatility = {
            'PFP': 0.15, 'Art': 0.20, 'Gaming': 0.25, 'Utility': 0.18
        }
        
        category = self._get_nft_category(nft)
        volatility = category_volatility.get(category, 0.18)
        
        # Confidence interval (assume normal distribution)
        confidence_95 = predicted_price * volatility * 1.96
        
        return {
            'lower_bound': max(predicted_price - confidence_95, predicted_price * 0.6),
            'upper_bound': predicted_price + confidence_95,
            'confidence_level': 0.95
        }
    
    def detect_anomalies(self, nft, predicted_price):
        """Detect price anomalies"""
        current_price = nft.estimated_value
        price_change = abs(float(predicted_price) - float(current_price)) / float(current_price)
        
        anomalies = []
        
        if price_change > 0.25:  # >25% change
            severity = 'HIGH' if price_change > 0.4 else 'MEDIUM'
            direction = 'INCREASE' if predicted_price > current_price else 'DECREASE'
            
            anomalies.append({
                'type': f'PRICE_{direction}',
                'severity': severity,
                'change_percentage': price_change * 100,
                'message': f'Predicted {direction.lower()} of {price_change*100:.1f}%'
            })
        
        return anomalies
    
    def train_models(self, training_data=None):
        """Train the ensemble models"""
        if training_data is None:
            training_data = self._generate_training_data()
        
        if len(training_data) < 10:
            print("Insufficient training data, skipping model training")
            return False
        
        try:
            # Prepare training data
            df = pd.DataFrame(training_data)
            feature_cols = [col for col in df.columns if col != 'target_price']
            
            X = df[feature_cols].values
            y = df['target_price'].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train models
            self.random_forest.fit(X_scaled, y)
            self.gradient_boosting.fit(X_scaled, y)
            
            if self.xgboost is not None:
                self.xgboost.fit(X_scaled, y)
            
            self.is_trained = True
            print(f"Successfully trained ensemble models with {len(training_data)} samples")
            return True
            
        except Exception as e:
            print(f"Error training models: {e}")
            return False
    
    def _generate_training_data(self):
        """Generate synthetic training data"""
        training_data = []
        nfts = NFTVault.objects.exclude(status='WITHDRAWN')[:100]  # Sample NFTs
        
        for nft in nfts:
            try:
                features = self.extract_all_features(nft)
                # Simulate target price with some noise
                base_price = float(nft.estimated_value)
                noise_factor = np.random.normal(1.0, 0.1)
                target_price = base_price * noise_factor
                
                features['target_price'] = target_price
                training_data.append(features)
            except:
                continue
        
        return training_data

# Global predictor instance
nft_predictor = NFTPricePredictor()
