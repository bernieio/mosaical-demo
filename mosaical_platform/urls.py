from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('nfts/', views.nft_list, name='nft_list'),
    path('nfts/deposit/', views.deposit_nft, name='deposit_nft'),
    path('loans/', views.loan_list, name='loan_list'),
    path('loans/create/', views.create_loan, name='create_loan'),

    # Hidden faucet - no UI links to this
    path('hidden-faucet-vbtc-url/', views.hidden_faucet, name='hidden_faucet'),
    path('dpo-marketplace/', views.dpo_marketplace, name='dpo_marketplace'),
    path('create-dpo/', views.create_dpo, name='create_dpo'),
    path('buy-dpo/', views.buy_dpo, name='buy_dpo'),
    path('update-dpo-price/', views.update_dpo_price, name='update_dpo_price'),
    # Loan repayment
    path('repay-loan/', views.repay_loan, name='repay_loan'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('nfts/', views.nft_list, name='nft_list'),
    path('deposit/', views.deposit_nft, name='deposit_nft'),
    path('loans/', views.loan_list, name='loan_list'),
    path('create-loan/', views.create_loan, name='create_loan'),
    path('repay-loan/', views.repay_loan, name='repay_loan'),
    path('dpo-marketplace/', views.dpo_marketplace, name='dpo_marketplace'),
    path('create-dpo/', views.create_dpo, name='create_dpo'),
    path('buy-dpo/', views.buy_dpo, name='buy_dpo'),
    path('update-dpo-price/', views.update_dpo_price, name='update_dpo_price'),
    path('hidden-faucet-vbtc-url/', views.hidden_faucet, name='hidden_faucet'),
    path('register/', views.register_view, name='register'),
    
    # Notification endpoints
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]
