from django.contrib import admin
from .models import Wallet, Card, BankAccount

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'is_active', 'is_locked', 'created_at')
    list_filter = ('is_active', 'is_locked', 'created_at')
    search_fields = ('user__email', 'user__phone_number')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('id', 'user')
        }),
        ('Balance Information', {
            'fields': ('balance',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_locked', 'lock_reason')
        }),
        ('Limits', {
            'fields': ('daily_limit', 'monthly_limit')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'card_type', 'mask_card_number', 'status', 'created_at')
    list_filter = ('card_type', 'status', 'created_at')
    search_fields = ('wallet__user__email', 'card_number', 'card_holder')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('Card Information', {
            'fields': ('id', 'wallet', 'card_number', 'card_holder', 'expiry_month', 'expiry_year', 'cvv')
        }),
        ('Card Details', {
            'fields': ('card_type', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'bank_name', 'mask_account_number', 'is_primary', 'is_verified')
    list_filter = ('is_primary', 'is_verified', 'created_at')
    search_fields = ('wallet__user__email', 'bank_name', 'account_number', 'account_holder')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Account Information', {
            'fields': ('wallet', 'bank_name', 'account_number', 'account_holder', 'account_type')
        }),
        ('Status', {
            'fields': ('is_primary', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
