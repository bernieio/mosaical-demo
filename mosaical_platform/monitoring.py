
from django.db import models
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from decimal import Decimal
import time

class PerformanceMetric(models.Model):
    METRIC_TYPES = [
        ('RESPONSE_TIME', 'Response Time'),
        ('DATABASE_QUERY', 'Database Query Time'),
        ('CACHE_HIT_RATE', 'Cache Hit Rate'),
        ('TRANSACTION_VOLUME', 'Transaction Volume'),
        ('USER_ACTIVITY', 'User Activity'),
    ]
    
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=15, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=200, blank=True)
    user_count = models.IntegerField(default=1)
    
    class Meta:
        indexes = [
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]

class PerformanceMonitor:
    """Performance monitoring utility"""
    
    @staticmethod
    def record_response_time(endpoint, duration, user_count=1):
        """Record API response time"""
        PerformanceMetric.objects.create(
            metric_type='RESPONSE_TIME',
            value=Decimal(str(duration)),
            endpoint=endpoint,
            user_count=user_count
        )
    
    @staticmethod
    def record_database_performance():
        """Record database query performance"""
        query_count = len(connection.queries)
        total_time = sum(float(query['time']) for query in connection.queries)
        
        PerformanceMetric.objects.create(
            metric_type='DATABASE_QUERY',
            value=Decimal(str(total_time)),
            user_count=query_count
        )
    
    @staticmethod
    def get_system_health():
        """Get overall system health metrics"""
        now = timezone.now()
        hour_ago = now - timezone.timedelta(hours=1)
        
        # Get recent metrics
        recent_metrics = PerformanceMetric.objects.filter(
            timestamp__gte=hour_ago
        )
        
        # Calculate averages
        avg_response_time = recent_metrics.filter(
            metric_type='RESPONSE_TIME'
        ).aggregate(avg=models.Avg('value'))['avg'] or 0
        
        total_transactions = recent_metrics.filter(
            metric_type='TRANSACTION_VOLUME'
        ).aggregate(sum=models.Sum('value'))['sum'] or 0
        
        return {
            'avg_response_time': float(avg_response_time),
            'hourly_transactions': float(total_transactions),
            'active_users': cache.get('active_users_count', 0),
            'system_status': 'healthy' if avg_response_time < 2.0 else 'slow'
        }

class PerformanceMiddleware:
    """Middleware to track response times"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        
        # Record response time for important endpoints
        important_endpoints = [
            'deposit_nft', 'create_loan', 'repay_loan', 
            'buy_dpo', 'dashboard', 'transaction_history'
        ]
        
        if any(endpoint in request.path for endpoint in important_endpoints):
            duration = time.time() - start_time
            PerformanceMonitor.record_response_time(request.path, duration)
        
        return response
