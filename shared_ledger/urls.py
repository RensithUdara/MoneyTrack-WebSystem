from django.urls import path
from . import views

app_name = 'shared_ledger'

urlpatterns = [
    path('', views.SharedLedgerListView.as_view(), name='ledger_list'),
    path('create/', views.SharedLedgerCreateView.as_view(), name='create_ledger'),
    path('<uuid:pk>/', views.SharedLedgerDetailView.as_view(), name='ledger_detail'),
    path('<uuid:pk>/edit/', views.SharedLedgerUpdateView.as_view(), name='edit_ledger'),
    path('<uuid:pk>/invite/', views.InviteMemberView.as_view(), name='invite_member'),
    path('<uuid:pk>/members/', views.manage_members, name='manage_members'),
    path('<uuid:pk>/expenses/add/', views.SharedExpenseCreateView.as_view(), name='add_expense'),
    path('<uuid:pk>/expenses/<int:expense_id>/', views.SharedExpenseDetailView.as_view(), name='expense_detail'),
    path('<uuid:pk>/expenses/<int:expense_id>/edit/', views.SharedExpenseUpdateView.as_view(), name='edit_expense'),
    path('<uuid:pk>/expenses/<int:expense_id>/approve/', views.approve_expense, name='approve_expense'),
    path('<uuid:pk>/payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('<uuid:pk>/payments/add/', views.SharedPaymentCreateView.as_view(), name='add_payment'),
    path('<uuid:pk>/payments/<int:payment_id>/confirm/', views.confirm_payment, name='confirm_payment'),
    path('<uuid:pk>/balances/', views.ledger_balances, name='ledger_balances'),
    path('<uuid:pk>/settle/', views.settle_balances, name='settle_balances'),
    path('invite/<uuid:token>/', views.accept_invite, name='accept_invite'),
    path('join/<str:invite_code>/', views.join_with_code, name='join_with_code'),
]
