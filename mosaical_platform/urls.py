
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
]
