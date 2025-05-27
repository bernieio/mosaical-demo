from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
import hashlib

class RateLimitMiddleware:
    """Rate limiting middleware to prevent spam transactions"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'deposit_nft': {'requests': 5, 'window': 3600},  # 5 requests per hour
            'create_loan': {'requests': 10, 'window': 3600},  # 10 requests per hour
            'repay_loan': {'requests': 20, 'window': 3600},   # 20 requests per hour
            'hidden_faucet': {'requests': 1, 'window': 86400},  # 1 request per day
            'buy_dpo': {'requests': 50, 'window': 3600},      # 50 requests per hour
        }

    def __call__(self, request):
        # Check rate limits for specific endpoints
        if request.user.is_authenticated:
            path = request.path.strip('/')

            for endpoint, limits in self.rate_limits.items():
                if endpoint in path and request.method == 'POST':
                    if not self._check_rate_limit(request.user.id, endpoint, limits):
                        response = HttpResponse("Rate limit exceeded for {endpoint}. Try again later.", status=429)
                        return response

        response = self.get_response(request)
        return response

    def _check_rate_limit(self, user_id, endpoint, limits):
        """Check if user is within rate limits"""
        key = f"rate_limit:{user_id}:{endpoint}"
        current_requests = cache.get(key, 0)

        if current_requests >= limits['requests']:
            return False

        # Increment counter
        cache.set(key, current_requests + 1, limits['window'])
        return True