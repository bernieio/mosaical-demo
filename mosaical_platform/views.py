from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta
import secrets

from .models import (
    UserProfile, NFTCollection, NFTVault, Loan, YieldRecord, 
    Transaction, FaucetClaim, SystemSettings, DPOToken
)
from .notifications import NotificationManager

def home(request):
    """Homepage view"""
    collections = NFTCollection.objects.filter(is_active=True)
    context = {
        'collections': collections,
        'total_users': UserProfile.objects.count(),
        'total_loans': Loan.objects.filter(status='ACTIVE').count(),
    }
    return render(request, 'mosaical_platform/home.html', context)

def register_view(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, vbtc_balance=0)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    """User dashboard"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_nfts = NFTVault.objects.filter(owner=request.user).exclude(status='WITHDRAWN')
    user_loans = Loan.objects.filter(borrower=request.user, status='ACTIVE')
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:10]

    context = {
        'profile': profile,
        'user_nfts': user_nfts,
        'user_loans': user_loans,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'mosaical_platform/dashboard.html', context)

@login_required
def nft_list(request):
    """List user's NFTs"""
    user_nfts = NFTVault.objects.filter(owner=request.user).exclude(status='WITHDRAWN')
    return render(request, 'mosaical_platform/nft_list.html', {'user_nfts': user_nfts})

@login_required
def deposit_nft(request):
    """Deposit NFT into vault"""
    if request.method == 'POST':
        collection_id = request.POST.get('collection')
        token_id = request.POST.get('token_id')
        name = request.POST.get('name')
        estimated_value = Decimal(request.POST.get('estimated_value', '0'))
        utility_score = int(request.POST.get('utility_score', '50'))

        try:
            collection = NFTCollection.objects.get(id=collection_id)

            # Check if NFT already exists
            if NFTVault.objects.filter(collection=collection, token_id=token_id).exists():
                messages.error(request, 'This NFT already exists in the system!')
                return redirect('deposit_nft')

            # Create NFT vault entry
            nft = NFTVault.objects.create(
                owner=request.user,
                collection=collection,
                token_id=token_id,
                name=name,
                estimated_value=estimated_value,
                utility_score=utility_score,
                status='DEPOSITED'
            )

            # Record transaction
            Transaction.objects.create(
                user=request.user,
                transaction_type='DEPOSIT_NFT',
                related_nft=nft,
                description=f'Deposited NFT {collection.name} #{token_id}'
            )

            messages.success(request, f'NFT {name} deposited successfully!')
            return redirect('nft_list')

        except NFTCollection.DoesNotExist:
            messages.error(request, 'Invalid collection selected!')
        except Exception as e:
            messages.error(request, f'Error depositing NFT: {str(e)}')

    collections = NFTCollection.objects.filter(is_active=True)
    return render(request, 'mosaical_platform/deposit_nft.html', {'collections': collections})

@login_required
def loan_list(request):
    """List user's loans"""
    user_loans = Loan.objects.filter(borrower=request.user)
    return render(request, 'mosaical_platform/loan_list.html', {'user_loans': user_loans})

@login_required
def create_loan(request):
    """Create a new loan against NFT collateral"""
    if request.method == 'POST':
        nft_id = request.POST.get('nft_id')
        loan_amount = Decimal(request.POST.get('loan_amount', '0'))

        try:
            nft = NFTVault.objects.get(id=nft_id, owner=request.user, status='DEPOSITED')

            # Calculate maximum loan amount based on LTV
            max_loan = (nft.estimated_value * nft.collection.max_ltv_ratio) / 100

            if loan_amount > max_loan:
                messages.error(request, f'Loan amount exceeds maximum allowed: {max_loan} vBTC')
                return redirect('create_loan')

            # Create loan
            with transaction.atomic():
                loan = Loan.objects.create(
                    borrower=request.user,
                    nft_collateral=nft,
                    principal_amount=loan_amount,
                    current_debt=loan_amount,
                    ltv_ratio=(loan_amount / nft.estimated_value) * 100,
                    interest_rate=Decimal('5.00')  # Default 5% monthly
                )

                # Update NFT status
                nft.status = 'COLLATERALIZED'
                nft.save()

                # Add vBTC to user balance
                profile = UserProfile.objects.get(user=request.user)
                profile.vbtc_balance += loan_amount
                profile.save()

                # Record transaction
                Transaction.objects.create(
                    user=request.user,
                    transaction_type='LOAN_CREATE',
                    amount=loan_amount,
                    related_nft=nft,
                    related_loan=loan,
                    description=f'Created loan of {loan_amount} vBTC against {nft.collection.name} #{nft.token_id}'
                )

            messages.success(request, f'Loan of {loan_amount} vBTC created successfully!')
            return redirect('loan_list')

        except NFTVault.DoesNotExist:
            messages.error(request, 'Invalid NFT selected!')
        except Exception as e:
            messages.error(request, f'Error creating loan: {str(e)}')

    # Get available NFTs for collateral
    available_nfts = NFTVault.objects.filter(owner=request.user, status='DEPOSITED')
    return render(request, 'mosaical_platform/create_loan.html', {'available_nfts': available_nfts})

@login_required
def hidden_faucet(request):
    """Hidden faucet endpoint - only accessible via secret URL"""
    secret_key = request.GET.get('key')

    # Check if the secret key is valid (you can set this in admin)
    try:
        expected_key = SystemSettings.objects.get(key='FAUCET_SECRET_KEY').value
    except SystemSettings.DoesNotExist:
        expected_key = 'MOSAICAL_SECRET_2024'  # Default key

    if secret_key != expected_key:
        raise Http404("Page not found")

    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to use the faucet.')
        return redirect('login')

    # Check daily limit
    today = timezone.now().date()
    today_claims = FaucetClaim.objects.filter(
        user=request.user,
        claimed_at__date=today
    ).count()

    if today_claims >= 1:  # Limit 1 claim per day
        messages.error(request, 'You have already claimed from faucet today!')
        return render(request, 'mosaical_platform/faucet.html', {'can_claim': False})

    if request.method == 'POST':
        faucet_amount = Decimal('10.0')  # 10 vBTC per claim

        with transaction.atomic():
            # Add vBTC to user balance
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.vbtc_balance += faucet_amount
            profile.save()

            # Record faucet claim
            FaucetClaim.objects.create(
                user=request.user,
                amount=faucet_amount,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )

            # Record transaction
            Transaction.objects.create(
                user=request.user,
                transaction_type='FAUCET_CLAIM',
                amount=faucet_amount,
                description=f'Claimed {faucet_amount} vBTC from faucet'
            )

        messages.success(request, f'Successfully claimed {faucet_amount} vBTC!')
        return redirect('dashboard')

    return render(request, 'mosaical_platform/faucet.html', {'can_claim': True})

@login_required
def dpo_marketplace(request):
    """DPO Token Marketplace"""
    available_dpos = DPOToken.objects.filter(is_for_sale=True).exclude(owner=request.user)
    user_dpos = DPOToken.objects.filter(owner=request.user)
    user_nfts = NFTVault.objects.filter(owner=request.user, status='DEPOSITED')

    return render(request, 'mosaical_platform/dpo_marketplace.html', {
        'available_dpos': available_dpos,
        'user_dpos': user_dpos,
        'user_nfts': user_nfts
    })

@login_required
def create_dpo(request):
    """Create a new DPO token"""
    if request.method == 'POST':
        nft_id = request.POST.get('nft_id')
        ownership_percentage = Decimal(request.POST.get('ownership_percentage'))
        price = Decimal(request.POST.get('price'))

        nft = get_object_or_404(NFTVault, id=nft_id, owner=request.user)

        # Check if total DPO ownership doesn't exceed 100%
        existing_dpos = DPOToken.objects.filter(original_nft=nft)
        total_existing = sum(dpo.ownership_percentage for dpo in existing_dpos)

        if total_existing + ownership_percentage > 100:
            messages.error(request, 'Total DPO ownership cannot exceed 100%')
            return redirect('dpo_marketplace')

        # Create DPO token
        DPOToken.objects.create(
            original_nft=nft,
            owner=request.user,
            ownership_percentage=ownership_percentage,
            purchase_price=price,
            current_price=price,
            is_for_sale=True
        )

        # Record transaction
        Transaction.objects.create(
            user=request.user,
            transaction_type='DPO_CREATED',
            amount=Decimal('0'),
            related_nft=nft,
            description=f'Created DPO token: {ownership_percentage}% of {nft.collection.name} #{nft.token_id}'
        )

        messages.success(request, 'DPO token created successfully!')

    return redirect('dpo_marketplace')

@login_required
def buy_dpo(request):
    """Buy a DPO token"""
    if request.method == 'POST':
        dpo_id = request.POST.get('dpo_id')
        dpo = get_object_or_404(DPOToken, id=dpo_id, is_for_sale=True)

        if dpo.owner == request.user:
            messages.error(request, 'You cannot buy your own DPO token')
            return redirect('dpo_marketplace')

        profile = request.user.userprofile
        if profile.vbtc_balance < dpo.current_price:
            messages.error(request, 'Insufficient vBTC balance')
            return redirect('dpo_marketplace')

        with transaction.atomic():
            # Transfer payment
            profile.vbtc_balance -= dpo.current_price
            profile.save()

            seller_profile = dpo.owner.userprofile
            seller_profile.vbtc_balance += dpo.current_price
            seller_profile.save()

            # Transfer ownership
            dpo.owner = request.user
            dpo.purchase_price = dpo.current_price
            dpo.is_for_sale = False
            dpo.save()

            # Record transactions
            Transaction.objects.create(
                user=request.user,
                transaction_type='DPO_PURCHASE',
                amount=dpo.current_price,
                related_nft=dpo.original_nft,
                description=f'Purchased DPO token: {dpo.ownership_percentage}% of {dpo.original_nft.collection.name} #{dpo.original_nft.token_id}'
            )

            Transaction.objects.create(
                user=seller_profile.user,
                transaction_type='DPO_SALE',
                amount=dpo.current_price,
                related_nft=dpo.original_nft,
                description=f'Sold DPO token: {dpo.ownership_percentage}% of {dpo.original_nft.collection.name} #{dpo.original_nft.token_id}'
            )

        messages.success(request, 'DPO token purchased successfully!')

    return redirect('dpo_marketplace')

@login_required
def update_dpo_price(request):
    """Update DPO token price"""
    if request.method == 'POST':
        dpo_id = request.POST.get('dpo_id')
        new_price = Decimal(request.POST.get('new_price'))

        dpo = get_object_or_404(DPOToken, id=dpo_id, owner=request.user)
        dpo.current_price = new_price
        dpo.is_for_sale = True
        dpo.save()

        messages.success(request, 'DPO token price updated successfully!')

    return redirect('dpo_marketplace')

@login_required
def repay_loan(request):
    """Repay loan (partial or full)"""
    if request.method == 'POST':
        loan_id = request.POST.get('loan_id')
        repay_amount = Decimal(request.POST.get('repay_amount', '0'))

        try:
            loan = Loan.objects.get(id=loan_id, borrower=request.user, status='ACTIVE')
            profile = UserProfile.objects.get(user=request.user)

            if repay_amount <= 0 or repay_amount > loan.current_debt:
                messages.error(request, 'Invalid repayment amount!')
                return redirect('loan_list')

            if profile.vbtc_balance < repay_amount:
                messages.error(request, 'Insufficient vBTC balance!')
                return redirect('loan_list')

            with transaction.atomic():
                # Deduct from user balance
                profile.vbtc_balance -= repay_amount
                profile.save()

                # Update loan debt
                loan.current_debt -= repay_amount

                if loan.current_debt <= Decimal('0.00000001'):  # Fully repaid
                    loan.current_debt = Decimal('0')
                    loan.status = 'REPAID'

                    # Release NFT collateral
                    loan.nft_collateral.status = 'DEPOSITED'
                    loan.nft_collateral.save()

                loan.save()

                # Record transaction
                Transaction.objects.create(
                    user=request.user,
                    transaction_type='LOAN_REPAY',
                    amount=repay_amount,
                    related_nft=loan.nft_collateral,
                    related_loan=loan,
                    description=f'Repaid {repay_amount} vBTC for loan #{loan.id}'
                )

            if loan.status == 'REPAID':
                messages.success(request, f'Loan #{loan.id} fully repaid! NFT collateral released.')
            else:
                messages.success(request, f'Partial repayment of {repay_amount} vBTC completed.')

        except Loan.DoesNotExist:
            messages.error(request, 'Invalid loan selected!')
        except Exception as e:
            messages.error(request, f'Error processing repayment: {str(e)}')

    return redirect('loan_list')


@login_required
def get_notifications(request):
    """Get user notifications via AJAX"""
    notifications = NotificationManager.get_user_notifications(request.user)
    return JsonResponse({'notifications': notifications})

@login_required
def mark_notification_read(request):
    """Mark notification as read"""
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        NotificationManager.mark_as_read(request.user, notification_id)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
