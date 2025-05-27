
from django.shortcuts import render
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from decimal import InvalidOperation
import logging

logger = logging.getLogger(__name__)

def handle_404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def handle_500(request):
    """Custom 500 error handler"""
    logger.error(f"Internal server error for user {request.user} at {request.path}")
    return render(request, 'errors/500.html', status=500)

def handle_403(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)

class ErrorHandlerMixin:
    """Mixin for consistent error handling in views"""
    
    def handle_error(self, request, error, error_type="general"):
        """Handle different types of errors consistently"""
        error_messages = {
            'insufficient_balance': 'Insufficient vBTC balance for this transaction.',
            'invalid_nft': 'The selected NFT is invalid or not available.',
            'loan_not_found': 'The specified loan was not found.',
            'ltv_exceeded': 'Loan amount would exceed maximum LTV ratio.',
            'database_error': 'A database error occurred. Please try again.',
            'calculation_error': 'Error in financial calculations. Please check inputs.',
            'permission_denied': 'You do not have permission to perform this action.',
            'general': 'An unexpected error occurred. Please try again.'
        }
        
        message = error_messages.get(error_type, error_messages['general'])
        logger.error(f"Error in {request.path}: {str(error)}")
        
        return JsonResponse({
            'success': False,
            'error': message,
            'error_code': error_type
        }) if request.headers.get('Content-Type') == 'application/json' else message

def log_financial_error(user, action, error, details=None):
    """Log financial operation errors"""
    logger.error(f"Financial error - User: {user}, Action: {action}, Error: {str(error)}, Details: {details}")
