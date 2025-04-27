from django.urls import path
from . import views
from transactions.views import transaction_detail_view 

urlpatterns = [
    path('', views.wallet_detail_view, name='wallet_detail'),
    path('cards/add/', views.add_card_view, name='add_card'),
    path('cards/<uuid:card_id>/', views.card_detail_view, name='card_detail'),
    path('cards/<uuid:card_id>/toggle/', views.toggle_card_status_view, name='toggle_card_status'),
    path('bank-accounts/add/', views.add_bank_account_view, name='add_bank_account'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('transactions/<uuid:transaction_id>/', transaction_detail_view, name='transaction_detail'),
    path('search-recipient/', views.search_recipient, name='search_recipient'),
]
