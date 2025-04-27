from django.db import models, IntegrityError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

class Transaction(models.Model):
    """Model for all financial transactions."""
    TRANSACTION_TYPES = (
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('transfer_in', _('Transfer In')),
        ('transfer_out', _('Transfer Out')),
        ('payment', _('Payment')),
        ('refund', _('Refund')),
        ('cashback', _('Cashback')),
        ('mobile_recharge', _('Mobile Recharge')),
        ('bill_payment', _('Bill Payment')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey('wallet.Wallet', on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=50, unique=True)
    
    # For transfers
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_transactions')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transactions')
    
    # For bill payments
    bill_category = models.CharField(max_length=50, blank=True, null=True)
    bill_reference = models.CharField(max_length=50, blank=True, null=True)
    
    # For mobile recharges
    mobile_operator = models.CharField(max_length=50, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} - {self.status}"
    
    @property
    def is_credit(self):
        """Return True if transaction adds money to wallet."""
        return self.transaction_type in ['deposit', 'transfer_in', 'refund', 'cashback']
    
    @property
    def is_debit(self):
        """Return True if transaction removes money from wallet."""
        return not self.is_credit
    
    @classmethod
    def create_with_unique_reference(cls, **kwargs):
        """Create a transaction with a guaranteed unique reference"""
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # Generate a unique reference if not provided
                if 'reference' not in kwargs:
                    kwargs['reference'] = f"TRX-{uuid.uuid4().hex[:12].upper()}"
                
                # Create and return the transaction
                return cls.objects.create(**kwargs)
            except IntegrityError:
                if attempt == max_attempts - 1:
                    raise
                # If we get an IntegrityError, try again with a new reference
                if 'reference' in kwargs:
                    del kwargs['reference']  # Remove the existing reference to generate a new one
                continue


class TransactionReceipt(models.Model):
    """Model for transaction receipts."""
    
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='receipts/', null=True, blank=True)
    
    class Meta:
        verbose_name = _('Transaction Receipt')
        verbose_name_plural = _('Transaction Receipts')
    
    def __str__(self):
        return f"Receipt for {self.transaction.reference}"
