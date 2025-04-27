from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

class BillCategory(models.Model):
    """Categories for bill payments."""
    
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)  # CSS class for icon
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Bill Category')
        verbose_name_plural = _('Bill Categories')
    
    def __str__(self):
        return self.name


class BillProvider(models.Model):
    """Providers for bill payments."""
    
    name = models.CharField(max_length=100)
    category = models.ForeignKey(BillCategory, on_delete=models.CASCADE, related_name='providers')
    logo = models.ImageField(upload_to='provider_logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Fields required for payment
    account_number_label = models.CharField(max_length=100, default="Numéro de compte")
    account_number_regex = models.CharField(max_length=100, blank=True)
    additional_fields = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Bill Provider')
        verbose_name_plural = _('Bill Providers')
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


class MobileOperator(models.Model):
    """Mobile operators for recharges."""
    
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='operator_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Mobile Operator')
        verbose_name_plural = _('Mobile Operators')
    
    def __str__(self):
        return self.name


class DataPlan(models.Model):
    """Data plans for mobile operators."""
    
    operator = models.ForeignKey(MobileOperator, on_delete=models.CASCADE, related_name='data_plans')
    name = models.CharField(max_length=100)
    data_amount = models.CharField(max_length=50)
    validity = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Data Plan')
        verbose_name_plural = _('Data Plans')
    
    def __str__(self):
        return f"{self.operator.name} - {self.name} ({self.data_amount})"


class BillPayment(models.Model):
    """Model for bill payments."""
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bill_payments')
    provider = models.ForeignKey(BillProvider, on_delete=models.CASCADE, related_name='payments')
    account_number = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    additional_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transaction = models.OneToOneField('transactions.Transaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='bill_payment')
    
    class Meta:
        verbose_name = _('Bill Payment')
        verbose_name_plural = _('Bill Payments')
    
    def __str__(self):
        return f"{self.provider.name} - {self.account_number} - {self.amount}"


class MobileRecharge(models.Model):
    """Model for mobile recharges."""
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mobile_recharges')
    operator = models.ForeignKey(MobileOperator, on_delete=models.CASCADE, related_name='recharges')
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    data_plan = models.ForeignKey(DataPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='recharges')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transaction = models.OneToOneField('transactions.Transaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='mobile_recharge')
    
    class Meta:
        verbose_name = _('Mobile Recharge')
        verbose_name_plural = _('Mobile Recharges')
    
    def __str__(self):
        return f"{self.operator.name} - {self.phone_number} - {self.amount}"
