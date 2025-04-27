from django.urls import path
from . import views

urlpatterns = [
    path('history/', views.transaction_history_view, name='transaction_history'),
    path('<uuid:transaction_id>/', views.transaction_detail_view, name='transaction_detail'),
    path('<uuid:transaction_id>/receipt/', views.generate_receipt_view, name='generate_receipt'),
    path('export/', views.export_transactions_view, name='export_transactions'),
    path('search/', views.search_transactions_view, name='search_transactions'),
]
