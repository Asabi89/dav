from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

class Wallet(models.Model):
    """User wallet model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Wallet status
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    lock_reason = models.CharField(max_length=255, blank=True, null=True)
    
    # Wallet limits
    daily_limit = models.DecimalField(max_digits=12, decimal_places=2, default=1000)
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2, default=10000)
    
    class Meta:
        verbose_name = _('Wallet')
        verbose_name_plural = _('Wallets')
    
    def __str__(self):
        return f"Wallet for {self.user.email}"
    
    def deposit(self, amount):
        """Add funds to wallet."""
        self.balance += amount
        self.save()
        return True
    
    def withdraw(self, amount):
        """Remove funds from wallet if sufficient balance."""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False
    
    def can_withdraw(self, amount):
        """Check if withdrawal is possible."""
        return self.balance >= amount and not self.is_locked and self.is_active


class Card(models.Model):
    """Virtual or physical card linked to wallet."""
    
    CARD_TYPES = (
        ('virtual', _('Virtual Card')),
        ('physical', _('Physical Card')),
    )
    
    CARD_STATUS = (
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('blocked', _('Blocked')),
        ('expired', _('Expired')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=16)
    card_holder = models.CharField(max_length=255)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    cvv = models.CharField(max_length=3)
    card_type = models.CharField(max_length=10, choices=CARD_TYPES, default='virtual')
    status = models.CharField(max_length=10, choices=CARD_STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Card')
        verbose_name_plural = _('Cards')
    
    def __str__(self):
        return f"{self.card_type.title()} Card **** **** **** {self.card_number[-4:]}"
    
    def mask_card_number(self):
        """Return masked card number for display."""
        return f"**** **** **** {self.card_number[-4:]}"
    
    def is_active(self):
        """Check if card is active."""
        return self.status == 'active'


class BankAccount(models.Model):
    """Bank account linked to wallet for deposits/withdrawals."""
    
    ACCOUNT_TYPES = (
        ('checking', _('Checking Account')),
        ('savings', _('Savings Account')),
    )
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=30)
    account_holder = models.CharField(max_length=255)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='checking')
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')
    
    def __str__(self):
        return f"{self.bank_name} - {self.mask_account_number()}"
    
    def mask_account_number(self):
        """Return masked account number for display."""
        if len(self.account_number) <= 4:
            return self.account_number
        return f"****{self.account_number[-4:]}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary account per wallet
        if self.is_primary:
            BankAccount.objects.filter(wallet=self.wallet, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
