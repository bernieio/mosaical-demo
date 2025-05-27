
from decimal import Decimal
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q
from datetime import timedelta
import json
from .models import NFTVault, NFTCollection, Transaction, Loan, DPOToken
from .ai_models import nft_predictor

class MarketIntelligence:
    """Advanced market analysis with AI insights"""
    
    @staticmethod
    def generate_market_report(days=30):
        """Generate comprehensive market intelligence report"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        report = {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'market_overview': MarketIntelligence._get_market_overview(start_date),
            'collection_analysis': MarketIntelligence._analyze_collections(start_date),
            'price_predictions': MarketIntelligence._get_price_predictions(),
            'risk_assessment': MarketIntelligence._assess_market_risks(),
            'anomaly_detection': MarketIntelligence._detect_market_anomalies(),
            'recommendations': MarketIntelligence._generate_recommendations(),
            'generated_at': timezone.now().isoformat()
        }
        
        return report
    
    @staticmethod
    def _get_market_overview(start_date):
        """Get overall market metrics"""
        total_nfts = NFTVault.objects.exclude(status='WITHDRAWN').count()
        total_value = NFTVault.objects.exclude(status='WITHDRAWN').aggregate(
            sum=Sum('estimated_value')
        )['sum'] or Decimal('0')
        
        recent_transactions = Transaction.objects.filter(created_at__gte=start_date)
        transaction_volume = recent_transactions.count()
        
        active_loans = Loan.objects.filter(status='ACTIVE').count()
        total_debt = Loan.objects.filter(status='ACTIVE').aggregate(
            sum=Sum('current_debt')
        )['sum'] or Decimal('0')
        
        return {
            'total_nfts': total_nfts,
            'total_value_vbtc': float(total_value),
            'transaction_count': transaction_volume,
            'active_loans': active_loans,
            'total_debt_vbtc': float(total_debt),
            'average_ltv': float(total_debt / total_value * 100) if total_value > 0 else 0,
        }
    
    @staticmethod
    def _analyze_collections(start_date):
        """Analyze performance by collection"""
        collections = NFTCollection.objects.filter(is_active=True)
        analysis = []
        
        for collection in collections:
            nfts = NFTVault.objects.filter(collection=collection).exclude(status='WITHDRAWN')
            
            if nfts.exists():
                total_value = nfts.aggregate(sum=Sum('estimated_value'))['sum'] or Decimal('0')
                avg_value = nfts.aggregate(avg=Avg('estimated_value'))['avg'] or Decimal('0')
                
                # Get recent transactions
                recent_txs = Transaction.objects.filter(
                    related_nft__collection=collection,
                    created_at__gte=start_date
                ).count()
                
                # Calculate AI prediction metrics
                predictions = []
                confidences = []
                
                for nft in nfts[:10]:  # Sample first 10 NFTs
                    try:
                        pred_price = nft_predictor.predict_price(nft)
                        current_price = nft.estimated_value
                        change = float((pred_price - current_price) / current_price * 100)
                        predictions.append(change)
                        
                        # Calculate confidence
                        ci = nft_predictor.calculate_confidence_interval(nft, pred_price)
                        confidence = 1 - (float(ci['upper_bound'] - ci['lower_bound']) / float(pred_price))
                        confidences.append(confidence)
                    except:
                        continue
                
                avg_prediction = sum(predictions) / len(predictions) if predictions else 0
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                analysis.append({
                    'collection_name': collection.name,
                    'total_nfts': nfts.count(),
                    'total_value_vbtc': float(total_value),
                    'average_value_vbtc': float(avg_value),
                    'recent_activity': recent_txs,
                    'predicted_change_percent': round(avg_prediction, 2),
                    'prediction_confidence': round(avg_confidence, 2),
                    'max_ltv': float(collection.max_ltv_ratio),
                    'yield_rate': float(collection.base_yield_rate)
                })
        
        return sorted(analysis, key=lambda x: x['total_value_vbtc'], reverse=True)
    
    @staticmethod
    def _get_price_predictions():
        """Get AI price predictions for top NFTs"""
        top_nfts = NFTVault.objects.exclude(status='WITHDRAWN').order_by('-estimated_value')[:20]
        predictions = []
        
        for nft in top_nfts:
            try:
                predicted_price = nft_predictor.predict_price(nft)
                current_price = nft.estimated_value
                change_percent = float((predicted_price - current_price) / current_price * 100)
                
                ci = nft_predictor.calculate_confidence_interval(nft, predicted_price)
                anomalies = nft_predictor.detect_anomalies(nft, predicted_price)
                
                predictions.append({
                    'nft_id': nft.id,
                    'nft_name': f"{nft.collection.name} #{nft.token_id}",
                    'current_price_vbtc': float(current_price),
                    'predicted_price_vbtc': float(predicted_price),
                    'change_percent': round(change_percent, 2),
                    'confidence_interval': {
                        'lower': float(ci['lower_bound']),
                        'upper': float(ci['upper_bound'])
                    },
                    'anomalies': anomalies,
                    'recommendation': MarketIntelligence._get_nft_recommendation(change_percent, anomalies)
                })
            except Exception as e:
                continue
        
        return sorted(predictions, key=lambda x: abs(x['change_percent']), reverse=True)
    
    @staticmethod
    def _assess_market_risks():
        """Assess overall market risks"""
        risks = []
        
        # Liquidation risk
        at_risk_loans = Loan.objects.filter(status='ACTIVE', ltv_ratio__gte=75).count()
        total_loans = Loan.objects.filter(status='ACTIVE').count()
        liquidation_risk = (at_risk_loans / total_loans * 100) if total_loans > 0 else 0
        
        if liquidation_risk > 20:
            risks.append({
                'type': 'LIQUIDATION_RISK',
                'severity': 'HIGH' if liquidation_risk > 40 else 'MEDIUM',
                'value': round(liquidation_risk, 1),
                'description': f'{liquidation_risk:.1f}% of loans at liquidation risk (LTV >= 75%)'
            })
        
        # Concentration risk
        collections = NFTCollection.objects.filter(is_active=True)
        total_value = NFTVault.objects.exclude(status='WITHDRAWN').aggregate(
            sum=Sum('estimated_value')
        )['sum'] or Decimal('0')
        
        for collection in collections:
            collection_value = NFTVault.objects.filter(collection=collection).exclude(
                status='WITHDRAWN'
            ).aggregate(sum=Sum('estimated_value'))['sum'] or Decimal('0')
            
            concentration = float(collection_value / total_value * 100) if total_value > 0 else 0
            
            if concentration > 30:
                risks.append({
                    'type': 'CONCENTRATION_RISK',
                    'severity': 'HIGH' if concentration > 50 else 'MEDIUM',
                    'value': round(concentration, 1),
                    'description': f'{collection.name} represents {concentration:.1f}% of total value'
                })
        
        # Yield sustainability risk
        total_debt = Loan.objects.filter(status='ACTIVE').aggregate(
            sum=Sum('current_debt')
        )['sum'] or Decimal('0')
        
        if total_value > 0:
            debt_ratio = float(total_debt / total_value * 100)
            if debt_ratio > 60:
                risks.append({
                    'type': 'YIELD_SUSTAINABILITY_RISK',
                    'severity': 'HIGH' if debt_ratio > 80 else 'MEDIUM',
                    'value': round(debt_ratio, 1),
                    'description': f'High debt-to-value ratio: {debt_ratio:.1f}%'
                })
        
        return risks
    
    @staticmethod
    def _detect_market_anomalies():
        """Detect market-wide anomalies"""
        anomalies = []
        
        # Check for unusual price movements
        recent_nfts = NFTVault.objects.exclude(status='WITHDRAWN').order_by('-deposit_date')[:50]
        
        large_predictions = []
        for nft in recent_nfts:
            try:
                predicted_price = nft_predictor.predict_price(nft)
                nft_anomalies = nft_predictor.detect_anomalies(nft, predicted_price)
                
                for anomaly in nft_anomalies:
                    if anomaly['severity'] in ['HIGH', 'MEDIUM']:
                        large_predictions.append({
                            'nft_name': f"{nft.collection.name} #{nft.token_id}",
                            'anomaly': anomaly
                        })
            except:
                continue
        
        if large_predictions:
            anomalies.append({
                'type': 'PRICE_ANOMALIES',
                'count': len(large_predictions),
                'description': f'Detected {len(large_predictions)} significant price anomalies',
                'examples': large_predictions[:5]
            })
        
        # Check for unusual transaction patterns
        recent_transactions = Transaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count()
        
        avg_daily_transactions = Transaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count() / 7
        
        if recent_transactions > avg_daily_transactions * 2:
            anomalies.append({
                'type': 'TRANSACTION_SPIKE',
                'value': recent_transactions,
                'description': f'Unusual transaction activity: {recent_transactions} vs {avg_daily_transactions:.1f} average'
            })
        
        return anomalies
    
    @staticmethod
    def _generate_recommendations():
        """Generate AI-driven market recommendations"""
        recommendations = []
        
        # Collection recommendations
        collections = NFTCollection.objects.filter(is_active=True)
        
        for collection in collections:
            nfts = NFTVault.objects.filter(collection=collection).exclude(status='WITHDRAWN')
            
            if nfts.count() >= 3:
                predictions = []
                for nft in nfts[:10]:
                    try:
                        pred_price = nft_predictor.predict_price(nft)
                        current_price = nft.estimated_value
                        change = float((pred_price - current_price) / current_price * 100)
                        predictions.append(change)
                    except:
                        continue
                
                if predictions:
                    avg_prediction = sum(predictions) / len(predictions)
                    
                    if avg_prediction > 15:
                        recommendations.append({
                            'type': 'BUY',
                            'target': collection.name,
                            'confidence': 'HIGH' if avg_prediction > 25 else 'MEDIUM',
                            'expected_return': f'+{avg_prediction:.1f}%',
                            'reason': f'AI predicts {avg_prediction:.1f}% price increase'
                        })
                    elif avg_prediction < -15:
                        recommendations.append({
                            'type': 'SELL',
                            'target': collection.name,
                            'confidence': 'HIGH' if avg_prediction < -25 else 'MEDIUM',
                            'expected_return': f'{avg_prediction:.1f}%',
                            'reason': f'AI predicts {avg_prediction:.1f}% price decrease'
                        })
        
        # Risk management recommendations
        high_ltv_loans = Loan.objects.filter(status='ACTIVE', ltv_ratio__gte=80).count()
        if high_ltv_loans > 0:
            recommendations.append({
                'type': 'RISK_MANAGEMENT',
                'target': 'High LTV Loans',
                'confidence': 'HIGH',
                'action': 'Monitor closely or partial liquidation',
                'reason': f'{high_ltv_loans} loans with LTV >= 80%'
            })
        
        return recommendations
    
    @staticmethod
    def _get_nft_recommendation(change_percent, anomalies):
        """Get recommendation for individual NFT"""
        if change_percent > 20:
            return 'STRONG_BUY'
        elif change_percent > 10:
            return 'BUY'
        elif change_percent > -10:
            return 'HOLD'
        elif change_percent > -20:
            return 'SELL'
        else:
            return 'STRONG_SELL'
    
    @staticmethod
    def get_user_portfolio_analysis(user):
        """Generate personalized portfolio analysis"""
        user_nfts = NFTVault.objects.filter(owner=user).exclude(status='WITHDRAWN')
        user_loans = Loan.objects.filter(borrower=user, status='ACTIVE')
        
        portfolio = {
            'total_nfts': user_nfts.count(),
            'total_value': 0,
            'predicted_value': 0,
            'total_debt': 0,
            'health_score': 0,
            'recommendations': [],
            'risk_factors': []
        }
        
        if not user_nfts.exists():
            return portfolio
        
        total_current = Decimal('0')
        total_predicted = Decimal('0')
        
        for nft in user_nfts:
            current_price = nft.estimated_value
            total_current += current_price
            
            try:
                predicted_price = nft_predictor.predict_price(nft)
                total_predicted += predicted_price
                
                change_percent = float((predicted_price - current_price) / current_price * 100)
                
                if abs(change_percent) > 15:
                    recommendation = MarketIntelligence._get_nft_recommendation(change_percent, [])
                    portfolio['recommendations'].append({
                        'nft': f"{nft.collection.name} #{nft.token_id}",
                        'action': recommendation,
                        'expected_change': f'{change_percent:+.1f}%'
                    })
            except:
                total_predicted += current_price
        
        portfolio['total_value'] = float(total_current)
        portfolio['predicted_value'] = float(total_predicted)
        portfolio['expected_return'] = float((total_predicted - total_current) / total_current * 100) if total_current > 0 else 0
        
        # Calculate debt and health
        total_debt = user_loans.aggregate(sum=Sum('current_debt'))['sum'] or Decimal('0')
        portfolio['total_debt'] = float(total_debt)
        
        if total_current > 0:
            ltv_ratio = float(total_debt / total_current * 100)
            portfolio['ltv_ratio'] = ltv_ratio
            portfolio['health_score'] = max(0, 100 - ltv_ratio)
            
            if ltv_ratio > 75:
                portfolio['risk_factors'].append('High LTV ratio - liquidation risk')
            if ltv_ratio > 60:
                portfolio['risk_factors'].append('Monitor debt levels closely')
        
        return portfolio
