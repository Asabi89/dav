from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction

from .models import BillCategory, BillProvider, MobileOperator, DataPlan, BillPayment, MobileRecharge
from .forms import BillPaymentForm, MobileRechargeForm
from wallet.models import Wallet
from transactions.models import Transaction
from django.db import transaction


@login_required
def bill_categories_view(request):
    """View bill payment categories."""
    categories = BillCategory.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'payments/bill_categories.html', context)


@login_required
def bill_providers_view(request, category_id):
    """View bill providers for a category."""
    category = get_object_or_404(BillCategory, id=category_id, is_active=True)
    providers = BillProvider.objects.filter(category=category, is_active=True)
    
    context = {
        'category': category,
        'providers': providers,
    }
    
  
    return render(request, 'payments/bill_providers.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import   BillProvider, BillPayment
from wallet.models import Wallet
from transactions.models import Transaction
from .forms import BillPaymentForm
from accounts.services import create_notification
from django.urls import reverse

@login_required
def bill_payment_view(request, provider_id=None):
    """Pay a bill."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    # Pre-select provider if specified
    initial = {}
    if provider_id:
        provider = get_object_or_404(BillProvider, id=provider_id, is_active=True)
        initial['provider'] = provider
    
    if request.method == 'POST':
        form = BillPaymentForm(request.POST)  # Remove initial=initial here
        if form.is_valid():
            amount = form.cleaned_data.get('amount')
            provider = form.cleaned_data.get('provider')
            account_number = form.cleaned_data.get('account_number')
            
            # Check if user has sufficient balance
            if not wallet.can_withdraw(amount):
                messages.error(request, "Solde insuffisant pour effectuer ce paiement.")
                return redirect('bill_payment')
            
            # Process payment
            with transaction.atomic():
                # Create bill payment
                bill_payment = form.save(commit=False)
                bill_payment.user = user
                bill_payment.status = 'completed'  # For demo, assume payment is successful
                bill_payment.save()
                
                # Remove money from wallet
                wallet.withdraw(amount)
                
                # Create transaction record
                transaction_obj = Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='bill_payment',
                    amount=amount,
                    status='completed',
                    description=f"Paiement de facture {bill_payment.provider.name}",
                    reference=f"BILL-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    bill_category=bill_payment.provider.category.name,
                    bill_reference=bill_payment.account_number
                )
                
                # Link transaction to bill payment
                bill_payment.transaction = transaction_obj
                bill_payment.save()
                
                # Create notification
                create_notification(
                    user=user,
                    notification_type='bill_payment',
                    title=f"Paiement de facture {provider.name}",
                    message=f"Votre paiement de {amount} FCFA pour {provider.name} (N° {account_number}) a été effectué avec succès.",
                    icon="file-invoice-dollar",
                    link=reverse('bill_payment_detail', args=[bill_payment.id])
                )
            
            messages.success(request, f"Paiement de {amount} FCFA effectué avec succès pour {bill_payment.provider.name}!")
            return redirect('bill_payment_success', payment_id=bill_payment.id)
    else:
        form = BillPaymentForm(initial=initial)
    
    context = {
        'form': form,
        'wallet': wallet,
    }
    
    return render(request, 'payments/bill_payment.html', context)


def bill_payment_detail_view(request, payment_id):
    """View details of a bill payment."""
    payment = get_object_or_404(BillPayment, id=payment_id)
    
    # Vérifier que l'utilisateur a le droit de voir ce paiement
    if payment.user != request.user:
        raise PermissionDenied
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/bill_payment_detail.html', context)


@login_required
def bill_payment_success_view(request, payment_id):
    """Bill payment success view."""
    user = request.user
    payment = get_object_or_404(BillPayment, id=payment_id, user=user)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/bill_payment_success.html', context)


@login_required
def mobile_operators_view(request):
    """View mobile operators."""
    operators = MobileOperator.objects.filter(is_active=True)
    
    context = {
        'operators': operators,
    }
    
    return render(request, 'payments/mobile_operators.html', context)

@login_required
def mobile_recharge_view(request, operator_id=None):
    """Recharge mobile."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    # Pre-select operator if specified
    initial = {}
    if operator_id:
        operator = get_object_or_404(MobileOperator, id=operator_id, is_active=True)
        initial['operator'] = operator
    
    if request.method == 'POST':
        form = MobileRechargeForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data.get('amount')
            
            # Check if user has sufficient balance
            if not wallet.can_withdraw(amount):
                messages.error(request, "Solde insuffisant pour effectuer cette recharge.")
                return redirect('mobile_recharge')
            
            # Process recharge
            with transaction.atomic():
                # Create mobile recharge
                recharge = form.save(commit=False)
                recharge.user = user
                recharge.status = 'completed'  # For demo, assume recharge is successful
                recharge.save()
                
                # Remove money from wallet
                wallet.withdraw(amount)
                
                # Create transaction record
                transaction_obj = Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='mobile_recharge',
                    amount=amount,
                    status='completed',
                    description=f"Recharge mobile {recharge.operator.name}",
                    reference=f"RECH-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    mobile_operator=recharge.operator.name,
                    mobile_number=recharge.phone_number
                )
                
                # Link transaction to recharge
                recharge.transaction = transaction_obj
                recharge.save()
                
                messages.success(request, f"Recharge de {amount} € effectuée avec succès pour {recharge.phone_number}!")
                return redirect('mobile_recharge_success', recharge_id=recharge.id)
    else:
        # For GET request, create a new form with initial data
        form = MobileRechargeForm(initial=initial)
    
    context = {
        'form': form,
        'wallet': wallet,
    }
    return render(request, 'payments/mobile_recharge.html', context)


@login_required
def mobile_recharge_success_view(request, recharge_id):
    """Mobile recharge success view."""
    user = request.user
    recharge = get_object_or_404(MobileRecharge, id=recharge_id, user=user)
    
    context = {
        'recharge': recharge,
    }
    
    return render(request, 'payments/mobile_recharge_success.html', context)


@login_required
def get_data_plans_view(request):
    """AJAX view to get data plans for an operator."""
    operator_id = request.GET.get('operator_id')
    
    if not operator_id:
        return JsonResponse({'error': 'Operator ID is required'}, status=400)
    
    try:
        data_plans = DataPlan.objects.filter(
            operator_id=operator_id, is_active=True
        ).values('id', 'name', 'data_amount', 'validity', 'price')
        
        return JsonResponse({'data_plans': list(data_plans)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
