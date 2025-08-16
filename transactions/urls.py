from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('add/', views.TransactionCreateView.as_view(), name='add_transaction'),
    path('<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='edit_transaction'),
    path('<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='delete_transaction'),
    path('import/', views.ImportTransactionsView.as_view(), name='import_transactions'),
    path('export/', views.export_transactions, name='export_transactions'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='add_category'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='edit_category'),
    path('merchants/', views.MerchantListView.as_view(), name='merchant_list'),
    path('merchants/add/', views.MerchantCreateView.as_view(), name='add_merchant'),
    path('merchants/<int:pk>/edit/', views.MerchantUpdateView.as_view(), name='edit_merchant'),
    path('recurring/', views.RecurringTransactionListView.as_view(), name='recurring_transactions'),
    path('recurring/add/', views.RecurringTransactionCreateView.as_view(), name='add_recurring'),
    path('recurring/<int:pk>/edit/', views.RecurringTransactionUpdateView.as_view(), name='edit_recurring'),
    path('api/categorize/', views.auto_categorize_transaction, name='auto_categorize'),
]
