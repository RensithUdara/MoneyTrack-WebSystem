from django.urls import path, include
from rest_framework.routers import DefaultRouter
from transactions.api import TransactionViewSet, CategoryViewSet
from budgets.api import BudgetViewSet, BudgetGoalViewSet
from dashboard.api import DashboardWidgetViewSet, NotificationViewSet
from analytics.api import FinancialInsightViewSet, SpendingPatternViewSet
from shared_ledger.api import SharedLedgerViewSet, SharedExpenseViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'budget-goals', BudgetGoalViewSet)
router.register(r'dashboard-widgets', DashboardWidgetViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'insights', FinancialInsightViewSet)
router.register(r'spending-patterns', SpendingPatternViewSet)
router.register(r'shared-ledgers', SharedLedgerViewSet)
router.register(r'shared-expenses', SharedExpenseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
