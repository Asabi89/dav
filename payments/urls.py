from django.urls import path
from . import views

urlpatterns = [
    # Bill payments
    path('bills/', views.bill_categories_view, name='bill_categories'),
    path('bills/category/<int:category_id>/', views.bill_providers_view, name='bill_providers'),
    path('bills/pay/', views.bill_payment_view, name='bill_payment'),
    path('bills/pay/<int:provider_id>/', views.bill_payment_view, name='bill_payment_provider'),
    path('bills/success/<uuid:payment_id>/', views.bill_payment_success_view, name='bill_payment_success'),
    path('bills/payment/<uuid:payment_id>/', views.bill_payment_detail_view, name='bill_payment_detail'),

    # Mobile recharges
    path('mobile/', views.mobile_operators_view, name='mobile_operators'),
    path('mobile/recharge/', views.mobile_recharge_view, name='mobile_recharge'),
    path('mobile/recharge/<int:operator_id>/', views.mobile_recharge_view, name='mobile_recharge_operator'),
    path('mobile/success/<uuid:recharge_id>/', views.mobile_recharge_success_view, name='mobile_recharge_success'),
    
    # AJAX endpoints
    path('api/data-plans/', views.get_data_plans_view, name='get_data_plans'),
]
