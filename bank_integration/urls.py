from django.urls import path
from . import views

app_name = 'bank_integration'

urlpatterns = [
    path('', views.BankAccountListView.as_view(), name='account_list'),
    path('add/', views.BankAccountCreateView.as_view(), name='add_account'),
    path('<int:pk>/edit/', views.BankAccountUpdateView.as_view(), name='edit_account'),
    path('<int:pk>/sync/', views.sync_account, name='sync_account'),
    path('<int:pk>/disconnect/', views.disconnect_account, name='disconnect_account'),
    path('banks/', views.BankListView.as_view(), name='bank_list'),
    path('sync-all/', views.sync_all_accounts, name='sync_all'),
    path('sync-status/', views.sync_status, name='sync_status'),
    path('api-logs/', views.APILogListView.as_view(), name='api_logs'),
    path('connect/<str:bank_code>/', views.connect_bank_account, name='connect_bank'),
]
