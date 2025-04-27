from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from .models import Wallet, Card, BankAccount
from .forms import CardForm, BankAccountForm, DepositForm, WithdrawForm
from transactions.models import Transaction




@login_required
def wallet_detail_view(request):
    """View wallet details."""
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Get cards and bank accounts
    cards = Card.objects.filter(wallet=wallet)
    bank_accounts = BankAccount.objects.filter(wallet=wallet)
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        wallet=wallet
    ).order_by('-timestamp')[:10]
    
    context = {
        'wallet': wallet,
        'cards': cards,
        'bank_accounts': bank_accounts,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'wallet/wallet_detail.html', context)


@login_required
def add_card_view(request):
    """Add a virtual card to wallet."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.wallet = wallet
            card.save()
            
            messages.success(request, "Carte ajoutée avec succès!")
            return redirect('wallet_detail')
    else:
        form = CardForm()
    
    return render(request, 'wallet/add_card.html', {'form': form})


@login_required
def card_detail_view(request, card_id):
    """View card details."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    card = get_object_or_404(Card, id=card_id, wallet=wallet)
    
    context = {
        'card': card,
    }
    
    return render(request, 'wallet/card_detail.html', context)

@login_required
def toggle_card_status_view(request, card_id):
    """Toggle card status (active/inactive) or block the card."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    card = get_object_or_404(Card, id=card_id, wallet=wallet)
    
    action = request.GET.get('action')
    
    if action == 'block':
        # Block the card permanently
        card.status = 'blocked'
        message = "Carte bloquée avec succès. Cette action est irréversible."
    else:
        # Toggle between active and inactive
        if card.status == 'active':
            card.status = 'inactive'
            message = "Carte désactivée avec succès."
        elif card.status == 'inactive':
            card.status = 'active'
            message = "Carte activée avec succès."
        # If the card is already blocked, don't change its status
        elif card.status == 'blocked':
            message = "Cette carte est bloquée et ne peut pas être réactivée."
    
    card.save()
    messages.success(request, message)
    return redirect('card_detail', card_id=card.id)


@login_required
def add_bank_account_view(request):
    """Add a bank account to wallet."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.wallet = wallet
            
            # For demo purposes, auto-verify the account
            bank_account.is_verified = True
            
            bank_account.save()
            
            messages.success(request, "Compte bancaire ajouté avec succès!")
            return redirect('wallet_detail')
    else:
        form = BankAccountForm()
    
    return render(request, 'wallet/add_bank_account.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Wallet
from transactions.models import Transaction
from .forms import DepositForm, WithdrawForm
from accounts.services import create_notification
from django.urls import reverse

@login_required
def deposit_view(request):
    """Deposit money into wallet."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    if request.method == 'POST':
        form = DepositForm(wallet, request.POST)
        if form.is_valid():
            amount = form.cleaned_data.get('amount')
            bank_account = form.cleaned_data.get('bank_account')
            
            # Stocker les données dans la session pour la confirmation
            request.session['operation_type'] = 'deposit'
            request.session['operation_data'] = {
                'amount': str(amount),
                'bank_account_id': bank_account.id,
                'bank_name': bank_account.bank_name
            }
            
            # Rediriger vers la confirmation
            return redirect('confirm_operation')
    else:
        form = DepositForm(wallet)
    
    return render(request, 'wallet/deposit.html', {'form': form, 'wallet': wallet})


def process_deposit(request, operation_data):
    """Process deposit after PIN confirmation."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    amount = Decimal(operation_data['amount'])
    bank_account_id = operation_data['bank_account_id']
    bank_name = operation_data['bank_name']
    
    bank_account = get_object_or_404(BankAccount, id=bank_account_id, wallet=wallet)
    
    # Process deposit (in a real app, this would involve payment gateway)
    with transaction.atomic():
        # Add money to wallet
        wallet.deposit(amount)
        
        # Create transaction record
        transaction_obj = Transaction.objects.create(
            wallet=wallet,
            transaction_type='deposit',
            amount=amount,
            status='completed',
            description=f"Dépôt depuis {bank_name}",
            reference=f"DEP-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        # Create notification
        create_notification(
            user=user,
            notification_type='deposit',
            title=f"Dépôt de {amount} FCFA effectué",
            message=f"Votre dépôt de {amount} FCFA depuis {bank_name} a été effectué avec succès.",
            link=reverse('transaction_detail', args=[transaction_obj.id])
        )
    
    # Nettoyer la session
    if 'operation_type' in request.session:
        del request.session['operation_type']
    if 'operation_data' in request.session:
        del request.session['operation_data']
    
    messages.success(request, f"{amount} FCFA déposés avec succès dans votre portefeuille!")
    return redirect('wallet_detail')


@login_required
def withdraw_view(request):
    """Withdraw money from wallet."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    if request.method == 'POST':
        form = WithdrawForm(wallet, request.POST)
        if form.is_valid():
            amount = form.cleaned_data.get('amount')
            bank_account = form.cleaned_data.get('bank_account')
            
            # Vérifier si le solde est suffisant
            if not wallet.can_withdraw(amount):
                messages.error(request, "Solde insuffisant pour effectuer ce retrait.")
                return redirect('withdraw')
            
            # Stocker les données dans la session pour la confirmation
            request.session['operation_type'] = 'withdraw'
            request.session['operation_data'] = {
                'amount': str(amount),
                'bank_account_id': bank_account.id,
                'bank_name': bank_account.bank_name
            }
            
            # Rediriger vers la confirmation
            return redirect('confirm_operation')
    else:
        form = WithdrawForm(wallet)
    
    return render(request, 'wallet/withdraw.html', {'form': form, 'wallet': wallet})


def process_withdrawal(request, operation_data):
    """Process withdrawal after PIN confirmation."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    amount = Decimal(operation_data['amount'])
    bank_account_id = operation_data['bank_account_id']
    bank_name = operation_data['bank_name']
    
    bank_account = get_object_or_404(BankAccount, id=bank_account_id, wallet=wallet)
    
    # Process withdrawal
    with transaction.atomic():
        # Remove money from wallet
        success = wallet.withdraw(amount)
        
        if success:
            # Create transaction record
            transaction_obj = Transaction.objects.create(
                wallet=wallet,
                transaction_type='withdrawal',
                amount=amount,
                status='completed',
                description=f"Retrait vers {bank_name}",
                reference=f"WIT-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            )
            
            # Create notification
            create_notification(
                user=user,
                notification_type='withdrawal',
                title=f"Retrait de {amount} FCFA effectué",
                message=f"Votre retrait de {amount} FCFA vers {bank_name} a été effectué avec succès.",
                link=reverse('transaction_detail', args=[transaction_obj.id])
            )
            
            # Nettoyer la session
            if 'operation_type' in request.session:
                del request.session['operation_type']
            if 'operation_data' in request.session:
                del request.session['operation_data']
            
            messages.success(request, f"{amount} FCFA retirés avec succès de votre portefeuille!")
            return redirect('wallet_detail')
        else:
            messages.error(request, "Solde insuffisant pour effectuer ce retrait.")
            return redirect('withdraw')


@login_required
def transfer_view(request):
    """Transfer money to another user."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    # Récupérer les transferts récents (5 derniers)
    recent_transfers = Transaction.objects.filter(
        wallet=wallet,
        transaction_type__in=['transfer_in', 'transfer_out']
    ).order_by('-timestamp')[:5]
    
    # Récupérer les destinataires récents (utilisateurs avec qui l'utilisateur a déjà effectué des transferts)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Trouver les utilisateurs à qui l'utilisateur actuel a envoyé de l'argent
    recipient_ids = Transaction.objects.filter(
        wallet=wallet,
        transaction_type='transfer_out'
    ).values_list('recipient_id', flat=True).distinct()
    
    # Récupérer les objets utilisateur correspondants
    recent_recipients = User.objects.filter(id__in=recipient_ids)[:6]
    
    if request.method == 'POST':
        recipient_identifier = request.POST.get('recipient')
        amount = Decimal(request.POST.get('amount', 0))
        description = request.POST.get('description', '')
        
        # Validate amount
        if amount <= 0:
            messages.error(request, "Le montant doit être supérieur à zéro.")
            return redirect('transfer')
        
        # Check if user has sufficient balance
        if not wallet.can_withdraw(amount):
            messages.error(request, "Solde insuffisant pour effectuer ce transfert.")
            return redirect('transfer')
        
        # Find recipient by email or phone
        try:
            # Try to find by email
            recipient_user = User.objects.get(email=recipient_identifier)
        except User.DoesNotExist:
            try:
                # Try to find by phone
                recipient_user = User.objects.get(phone_number=recipient_identifier)
            except User.DoesNotExist:
                messages.error(request, "Destinataire introuvable. Vérifiez l'email ou le numéro de téléphone.")
                return redirect('transfer')
        
        # Don't allow transfer to self
        if recipient_user == user:
            messages.error(request, "Vous ne pouvez pas transférer de l'argent à vous-même.")
            return redirect('transfer')
        
        # Stocker les données dans la session pour la confirmation
        request.session['operation_type'] = 'transfer'
        request.session['operation_data'] = {
            'amount': str(amount),
            'recipient_id': recipient_user.id,
            'recipient_email': recipient_user.email,
            'recipient_name': recipient_user.get_full_name() or recipient_user.email,
            'description': description
        }
        
        # Rediriger vers la confirmation
        return redirect('confirm_operation')
    
    context = {
        'wallet': wallet,
        'recent_transfers': recent_transfers,
        'recent_recipients': recent_recipients
    }
    
    return render(request, 'wallet/transfer.html', context)


def process_transfer(request, operation_data):
    """Process transfer after PIN confirmation."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    amount = Decimal(operation_data['amount'])
    recipient_id = operation_data['recipient_id']
    description = operation_data.get('description', '')
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    recipient_user = get_object_or_404(User, id=recipient_id)
    
    # Get or create recipient wallet
    recipient_wallet, created = Wallet.objects.get_or_create(user=recipient_user)
    
    # Process transfer
    with transaction.atomic():
        # Remove money from sender wallet
        wallet.withdraw(amount)
        
        # Add money to recipient wallet
        recipient_wallet.deposit(amount)
        
        # Create transaction records using the create_with_unique_reference method
        # Sender transaction
        sender_transaction = Transaction.create_with_unique_reference(
            wallet=wallet,
            transaction_type='transfer_out',
            amount=amount,
            status='completed',
            description=f"Transfert à {recipient_user.email}" + (f": {description}" if description else ""),
            recipient=recipient_user
        )
        
        # Recipient transaction
        recipient_transaction = Transaction.create_with_unique_reference(
            wallet=recipient_wallet,
            transaction_type='transfer_in',
            amount=amount,
            status='completed',
            description=f"Transfert de {user.email}" + (f": {description}" if description else ""),
            sender=user
        )
        
        # Create notification for sender
        create_notification(
            user=user,
            notification_type='transfer_sent',
            title=f"Transfert de {amount} FCFA envoyé",
            message=f"Vous avez envoyé {amount} FCFA à {recipient_user.get_full_name() or recipient_user.email}." +
                    (f" Message: {description}" if description else ""),
            link=reverse('transaction_detail', args=[sender_transaction.id])
        )
        
        # Create notification for recipient
        create_notification(
            user=recipient_user,
            notification_type='transfer_received',
            title=f"Transfert de {amount} FCFA reçu",
            message=f"Vous avez reçu {amount} FCFA de {user.get_full_name() or user.email}." +
                    (f" Message: {description}" if description else ""),
            link=reverse('transaction_detail', args=[recipient_transaction.id])
        )
    
    # Nettoyer la session
    if 'operation_type' in request.session:
        del request.session['operation_type']
    if 'operation_data' in request.session:
        del request.session['operation_data']
    
    messages.success(request, f"{amount} FCFA transférés avec succès à {recipient_user.email}!")
    return redirect('wallet_detail')




@login_required
def search_recipient(request):
    """Search for a recipient by email or phone number."""
    query = request.GET.get('query', '')
    
    if not query or len(query) < 3:
        return JsonResponse({'success': False, 'message': 'Veuillez entrer au moins 3 caractères'})
    
    User = get_user_model()
    
    # Rechercher l'utilisateur par email ou téléphone
    users = User.objects.filter(
        Q(email__icontains=query) | Q(phone_number__icontains=query)
    ).exclude(id=request.user.id)[:5]
    
    results = []
    for user in users:
        results.append({
            'id': user.id,
            'name': user.get_full_name() or user.email,
            'email': user.email,
            'phone': user.phone_number,
            'initials': user.get_initials(),
            'profile_picture': user.profile_picture.url if user.profile_picture else None
        })
    
    return JsonResponse({'success': True, 'results': results})