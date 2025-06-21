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

    # AI Features (using existing views)
    path('ai/market-intelligence/', views.ai_market_intelligence, name='ai_market_intelligence'),

    path('logout/', views.logout_view, name='logout'),
    # path('switch-currency/', views.switch_currency, name='switch_currency'),  # Removed - DPSV only
    # Hidden faucet - no UI links to this
    path('hidden-faucet-vbtc-url/', views.hidden_faucet, name='hidden_faucet'),

    # Notification endpoints
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    # AI & Analytics
    path('api/ai/predict/<int:nft_id>/', views.test_ai_prediction, name='test_ai_prediction'),
    path('api/ai/status/', views.ai_training_status, name='ai_training_status'),
    path('ai/train-models/', views.train_models, name='train_models'),
]