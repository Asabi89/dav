from django.contrib import admin
from .models import Transaction, TransactionReceipt

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'wallet', 'transaction_type', 'amount', 'status', 'timestamp')
    list_filter = ('transaction_type', 'status', 'timestamp')
    search_fields = ('reference', 'wallet__user__email', 'description')
    readonly_fields = ('id', 'timestamp')
    fieldsets = (
        ('Transaction Information', {
            'fields': ('id', 'wallet', 'transaction_type', 'amount', 'status', 'timestamp')
        }),
        ('Details', {
            'fields': ('description', 'reference')
        }),
        ('Transfer Information', {
            'fields': ('sender', 'recipient'),
            'classes': ('collapse',)
        }),
        ('Bill Payment', {
            'fields': ('bill_category', 'bill_reference'),
            'classes': ('collapse',)
        }),
        ('Mobile Recharge', {
            'fields': ('mobile_operator', 'mobile_number'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TransactionReceipt)
class TransactionReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'transaction', 'generated_at')
    search_fields = ('receipt_number', 'transaction__reference')
    readonly_fields = ('generated_at',)
