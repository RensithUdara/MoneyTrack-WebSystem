from django.db import models
from django.conf import settings
from django.utils import timezone
import json

class DashboardWidget(models.Model):
    """Configurable dashboard widgets"""
    
    WIDGET_TYPES = [
        ('account_balance', 'Account Balance'),
        ('monthly_summary', 'Monthly Summary'),
        ('spending_by_category', 'Spending by Category'),
        ('income_vs_expenses', 'Income vs Expenses'),
        ('budget_status', 'Budget Status'),
        ('recent_transactions', 'Recent Transactions'),
        ('financial_goals', 'Financial Goals'),
        ('cash_flow', 'Cash Flow'),
        ('spending_trends', 'Spending Trends'),
        ('alerts', 'Financial Alerts'),
    ]
    
    SIZE_CHOICES = [
        ('small', 'Small (1x1)'),
        ('medium', 'Medium (2x1)'),
        ('large', 'Large (2x2)'),
        ('wide', 'Wide (3x1)'),
        ('extra_large', 'Extra Large (3x2)'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_widgets')
    
    # Widget configuration
    widget_type = models.CharField(max_length=30, choices=WIDGET_TYPES)
    title = models.CharField(max_length=200)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='medium')
    
    # Position on dashboard
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    
    # Widget settings
    configuration = models.JSONField(default=dict, blank=True)
    is_visible = models.BooleanField(default=True)
    refresh_interval = models.PositiveIntegerField(default=300)  # seconds
    
    # Data caching
    cached_data = models.JSONField(blank=True, null=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_widget_type_display()}"
    
    def refresh_data(self):
        """Refresh widget data based on type"""
        from transactions.models import Transaction
        from bank_integration.models import BankAccount
        from budgets.models import Budget
        from datetime import datetime, timedelta
        
        now = timezone.now()
        data = {}
        
        if self.widget_type == 'account_balance':
            accounts = BankAccount.objects.filter(user=self.user, status='active')
            data = {
                'accounts': [
                    {
                        'name': acc.account_name,
                        'bank': acc.bank.name,
                        'balance': float(acc.current_balance),
                        'currency': acc.currency,
                    }
                    for acc in accounts
                ],
                'total_balance': float(sum(acc.current_balance for acc in accounts))
            }
        
        elif self.widget_type == 'monthly_summary':
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            transactions = Transaction.objects.filter(
                user=self.user,
                transaction_date__gte=start_of_month
            )
            
            total_income = sum(t.amount for t in transactions.filter(type='income'))
            total_expenses = sum(t.amount for t in transactions.filter(type='expense'))
            
            data = {
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'net_income': float(total_income - total_expenses),
                'transaction_count': transactions.count(),
            }
        
        elif self.widget_type == 'spending_by_category':
            thirty_days_ago = now - timedelta(days=30)
            expenses = Transaction.objects.filter(
                user=self.user,
                type='expense',
                transaction_date__gte=thirty_days_ago
            ).select_related('category')
            
            category_totals = {}
            for expense in expenses:
                cat_name = expense.category.name if expense.category else 'Uncategorized'
                category_totals[cat_name] = category_totals.get(cat_name, 0) + float(expense.amount)
            
            data = {
                'categories': [
                    {'name': name, 'amount': amount}
                    for name, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:10]
                ]
            }
        
        elif self.widget_type == 'budget_status':
            current_month = now.replace(day=1)
            budgets = Budget.objects.filter(
                user=self.user,
                status='active',
                period__start_date__lte=current_month,
                period__end_date__gte=current_month
            )
            
            budget_data = []
            for budget in budgets:
                budget.calculate_spent_amount()
                budget_data.append({
                    'name': budget.name,
                    'budgeted': float(budget.total_budget_amount),
                    'spent': float(budget.total_spent),
                    'remaining': float(budget.remaining_amount),
                    'percentage': budget.percentage_used,
                })
            
            data = {'budgets': budget_data}
        
        self.cached_data = data
        self.last_updated = now
        self.save()
        
        return data
    
    class Meta:
        db_table = 'dashboard_widgets'
        ordering = ['position_y', 'position_x']

class DashboardLayout(models.Model):
    """Dashboard layout configurations"""
    
    THEME_CHOICES = [
        ('dark', 'Dark Theme'),
        ('light', 'Light Theme'),
        ('auto', 'Auto (System)'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_layout')
    
    # Layout settings
    grid_columns = models.PositiveIntegerField(default=12)
    widget_margin = models.PositiveIntegerField(default=10)  # pixels
    
    # Theme and appearance
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='dark')
    sidebar_collapsed = models.BooleanField(default=False)
    show_help_tips = models.BooleanField(default=True)
    
    # Layout configuration
    layout_config = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dashboard Layout - {self.user.username}"
    
    class Meta:
        db_table = 'dashboard_layouts'

class UserPreference(models.Model):
    """User preferences and settings"""
    
    CURRENCY_DISPLAY_CHOICES = [
        ('symbol', 'Symbol (₨)'),
        ('code', 'Code (LKR)'),
        ('both', 'Both (₨ LKR)'),
    ]
    
    DATE_FORMAT_CHOICES = [
        ('DD/MM/YYYY', 'DD/MM/YYYY'),
        ('MM/DD/YYYY', 'MM/DD/YYYY'),
        ('YYYY-MM-DD', 'YYYY-MM-DD'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    
    # Display preferences
    currency_display_format = models.CharField(max_length=20, choices=CURRENCY_DISPLAY_CHOICES, default='symbol')
    date_format = models.CharField(max_length=20, choices=DATE_FORMAT_CHOICES, default='DD/MM/YYYY')
    number_format = models.CharField(max_length=20, default='1,234.56')
    
    # Functional preferences
    default_transaction_type = models.CharField(
        max_length=10,
        choices=[('expense', 'Expense'), ('income', 'Income')],
        default='expense'
    )
    auto_categorize_transactions = models.BooleanField(default=True)
    require_receipt_for_expenses = models.BooleanField(default=False)
    
    # Notification preferences
    enable_push_notifications = models.BooleanField(default=True)
    enable_email_notifications = models.BooleanField(default=True)
    enable_sms_notifications = models.BooleanField(default=False)
    
    # Budget preferences
    default_budget_period = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('weekly', 'Weekly'), ('quarterly', 'Quarterly')],
        default='monthly'
    )
    budget_alert_percentage = models.PositiveIntegerField(default=80)
    
    # Privacy preferences
    share_anonymous_usage_data = models.BooleanField(default=True)
    allow_data_export = models.BooleanField(default=True)
    
    # Language and localization
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='Asia/Colombo')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences - {self.user.username}"
    
    class Meta:
        db_table = 'user_preferences'

class Notification(models.Model):
    """System notifications"""
    
    NOTIFICATION_TYPES = [
        ('budget_alert', 'Budget Alert'),
        ('goal_update', 'Goal Update'),
        ('transaction_alert', 'Transaction Alert'),
        ('system_update', 'System Update'),
        ('shared_expense', 'Shared Expense'),
        ('payment_reminder', 'Payment Reminder'),
        ('insight', 'Financial Insight'),
        ('security', 'Security Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification content
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Metadata
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    data = models.JSONField(blank=True, null=True)  # Additional data
    
    # Related objects
    related_transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    related_budget = models.ForeignKey(
        'budgets.Budget',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    related_goal = models.ForeignKey(
        'budgets.BudgetGoal',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    
    # Delivery
    sent_via_email = models.BooleanField(default=False)
    sent_via_push = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def dismiss(self):
        self.is_dismissed = True
        self.dismissed_at = timezone.now()
        self.save()
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]
