from django.contrib import admin
from .models import BillCategory, BillProvider, MobileOperator, DataPlan, BillPayment, MobileRecharge

@admin.register(BillCategory)
class BillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(BillProvider)
class BillProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')


@admin.register(MobileOperator)
class MobileOperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(DataPlan)
class DataPlanAdmin(admin.ModelAdmin):
    list_display = ('operator', 'name', 'data_amount', 'validity', 'price', 'is_active')
    list_filter = ('operator', 'is_active')
    search_fields = ('name', 'data_amount')

@admin.register(BillPayment)
class BillPaymentAdmin(admin.ModelAdmin):
    list_display = ('provider', 'account_number', 'amount', 'status', 'created_at')
    list_filter = ('provider', 'status', 'created_at')
    search_fields = ('account_number', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(MobileRecharge)
class MobileRechargeAdmin(admin.ModelAdmin):
    list_display = ('operator', 'phone_number', 'amount', 'status', 'created_at')
    list_filter = ('operator', 'status', 'created_at')
    search_fields = ('phone_number', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
