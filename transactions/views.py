from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q
import csv
import io
from twilio.rest import Client
from .models import Transaction, TransactionReceipt
from wallet.models import Wallet
@login_required
def transaction_history_view(request):
    """View transaction history."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    # Get filter parameters
    transaction_type = request.GET.get('type', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    status = request.GET.get('status', '')
    min_amount = request.GET.get('min_amount', '')
    max_amount = request.GET.get('max_amount', '')
    reference = request.GET.get('reference', '')
    description = request.GET.get('description', '')
    
    # Base queryset
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-timestamp')
    
    # Apply filters
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if start_date:
        transactions = transactions.filter(timestamp__gte=start_date)
    if end_date:
        # Add one day to include the end date fully
        from datetime import datetime, timedelta
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj + timedelta(days=1)
            transactions = transactions.filter(timestamp__lt=end_date_obj)
        except ValueError:
            # If date parsing fails, use the original string
            transactions = transactions.filter(timestamp__lte=end_date)
    if status:
        transactions = transactions.filter(status=status)
    if min_amount:
        transactions = transactions.filter(amount__gte=min_amount)
    if max_amount:
        transactions = transactions.filter(amount__lte=max_amount)
    if reference:
        transactions = transactions.filter(reference__icontains=reference)
    if description:
        transactions = transactions.filter(description__icontains=description)
    
    # Calculate statistics for the summary
    from django.db.models import Sum, Avg, Q
    from decimal import Decimal
    
    # Filter the queryset for credit transactions (deposits and incoming transfers)
    credit_transactions = transactions.filter(
        Q(transaction_type='deposit') | 
        Q(transaction_type='transfer_in')
    )
    
    # Filter the queryset for debit transactions (withdrawals, outgoing transfers, bill payments, etc.)
    debit_transactions = transactions.filter(
        Q(transaction_type='withdrawal') | 
        Q(transaction_type='transfer_out') |
        Q(transaction_type='bill_payment') |
        Q(transaction_type='mobile_recharge')
    )
    
    # Calculate totals
    total_credit = credit_transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_debit = debit_transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    net_balance = total_credit - total_debit
    
    # Calculate average transaction amount
    average_amount = transactions.aggregate(Avg('amount'))['amount__avg'] or Decimal('0')
    if average_amount:
        average_amount = round(average_amount, 2)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    page = request.GET.get('page')
    transactions = paginator.get_page(page)
    
    # Get transaction types for filter dropdown
    transaction_types = Transaction.TRANSACTION_TYPES
    
    context = {
        'transactions': transactions,
        'transaction_types': transaction_types,
        'selected_type': transaction_type,
        'start_date': start_date,
        'end_date': end_date,
        # Statistics
        'total_credit': total_credit,
        'total_debit': total_debit,
        'net_balance': net_balance,
        'average_amount': average_amount,
    }
    
    return render(request, 'transactions/history.html', context)

@login_required
def transaction_detail_view(request, transaction_id):
    """View transaction details."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet=wallet)
    
    # Check if receipt exists
    try:
        receipt = transaction.receipt
    except TransactionReceipt.DoesNotExist:
        receipt = None
    
    context = {
        'transaction': transaction,
        'receipt': receipt,
    }
    
    return render(request, 'transactions/detail.html', context)


@login_required
def generate_receipt_view(request, transaction_id):
    """Generate receipt for transaction."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet=wallet)
    
    # Check if receipt already exists
    try:
        receipt = transaction.receipt
    except TransactionReceipt.DoesNotExist:
        # Generate receipt
        receipt_number = f"REC-{transaction.reference}"
        receipt = TransactionReceipt.objects.create(
            transaction=transaction,
            receipt_number=receipt_number
        )
        
        # In a real app, generate PDF here
        # For demo, we'll just redirect to receipt page
    
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def export_transactions_view(request):
    """Export transactions to CSV."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    # Get filter parameters
    transaction_type = request.GET.get('type', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Base queryset
    transactions = Transaction.objects.filter(wallet=wallet)
    
    # Apply filters
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if start_date:
        transactions = transactions.filter(timestamp__gte=start_date)
    
    if end_date:
        transactions = transactions.filter(timestamp__lte=end_date)
    
    # Create CSV file
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write header
    writer.writerow([
        'Date', 'Type', 'Montant', 'Statut', 'Description', 'Référence'
    ])
    
    # Write data
    for transaction in transactions:
        writer.writerow([
            transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.get_transaction_type_display(),
            transaction.amount,
            transaction.get_status_display(),
            transaction.description,
            transaction.reference
        ])
    
    # Prepare response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=transactions_{timezone.now().strftime("%Y%m%d")}.csv'
    
    return response


@login_required
def search_transactions_view(request):
    """Search transactions."""
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    
    query = request.GET.get('q', '')
    
    if query:
        transactions = Transaction.objects.filter(
            Q(wallet=wallet) &
            (Q(description__icontains=query) |
             Q(reference__icontains=query) |
             Q(amount__icontains=query))
        )
    else:
        transactions = Transaction.objects.none()
    
    context = {
        'transactions': transactions,
        'query': query,
    }
    
    return render(request, 'transactions/search.html', context)
