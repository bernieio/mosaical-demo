from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('nfts/', views.nft_list, name='nft_list'),
    path('nfts/deposit/', views.deposit_nft, name='deposit_nft'),
    path('loans/', views.loan_list, name='loan_list'),
    path('loans/create/', views.create_loan, name='create_loan'),
    path('repay-loan/', views.repay_loan, name='repay_loan'),
    path('dpo-marketplace/', views.dpo_marketplace, name='dpo_marketplace'),
    path('create-dpo/', views.create_dpo, name='create_dpo'),
    path('buy-dpo/', views.buy_dpo, name='buy_dpo'),
    path('update-dpo-price/', views.update_dpo_price, name='update_dpo_price'),
    path('refinance-loan/', views.refinance_loan, name='refinance_loan'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),
    path('export-transactions/', views.export_transactions, name='export_transactions'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('swap-collateral/', views.swap_collateral, name='swap_collateral'),

    # AI Features
    path('ai/market-intelligence/', views.ai_market_intelligence, name='ai_market_intelligence'),
    path('ai/portfolio-analysis/', views.ai_portfolio_analysis, name='ai_portfolio_analysis'),
    path('ai/risk-assessment/', views.ai_risk_assessment, name='ai_risk_assessment'),
    path('nft/<int:nft_id>/prediction/', views.nft_price_prediction, name='nft_price_prediction'),
    
    # API endpoints
    path('api/market-data/', views.api_market_data, name='api_market_data'),
    path('api/nft/<int:nft_id>/valuation/', views.api_nft_valuation, name='api_nft_valuation'),

    path('logout/', views.logout_view, name='logout'),

    # Hidden faucet - no UI links to this
    path('hidden-faucet-vbtc-url/', views.hidden_faucet, name='hidden_faucet'),

    # Notification endpoints
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]