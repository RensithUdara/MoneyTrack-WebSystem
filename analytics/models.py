from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json

class SpendingPattern(models.Model):
    """Analyzed spending patterns for ML insights"""
    
    PATTERN_TYPES = [
        ('monthly_trend', 'Monthly Trend'),
        ('category_preference', 'Category Preference'),
        ('merchant_frequency', 'Merchant Frequency'),
        ('time_based', 'Time-based Pattern'),
        ('seasonal', 'Seasonal Pattern'),
        ('anomaly', 'Spending Anomaly'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='spending_patterns')
    
    pattern_type = models.CharField(max_length=30, choices=PATTERN_TYPES)
    category = models.ForeignKey('transactions.Category', on_delete=models.CASCADE, null=True, blank=True)
    merchant = models.ForeignKey('transactions.Merchant', on_delete=models.CASCADE, null=True, blank=True)
    
    # Pattern data
    pattern_data = models.JSONField()  # Flexible data storage for different pattern types
    confidence_score = models.FloatField(default=0.0)  # ML confidence (0-1)
    
    # Time relevance
    analysis_period_start = models.DateField()
    analysis_period_end = models.DateField()
    
    # Pattern insights
    average_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    frequency = models.PositiveIntegerField(default=0)  # Times per period
    trend_direction = models.CharField(
        max_length=20,
        choices=[('increasing', 'Increasing'), ('decreasing', 'Decreasing'), ('stable', 'Stable')],
        default='stable'
    )
    
    # Recommendations
    recommendations = models.JSONField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_pattern_type_display()}"
    
    class Meta:
        db_table = 'spending_patterns'
        ordering = ['-confidence_score', '-created_at']
        indexes = [
            models.Index(fields=['user', 'pattern_type']),
            models.Index(fields=['category', 'analysis_period_start']),
        ]

class BudgetPrediction(models.Model):
    """AI-powered budget predictions and recommendations"""
    
    PREDICTION_TYPES = [
        ('monthly_budget', 'Monthly Budget Suggestion'),
        ('category_allocation', 'Category Allocation'),
        ('savings_potential', 'Savings Potential'),
        ('expense_forecast', 'Expense Forecast'),
        ('income_projection', 'Income Projection'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='budget_predictions')
    
    prediction_type = models.CharField(max_length=30, choices=PREDICTION_TYPES)
    category = models.ForeignKey('transactions.Category', on_delete=models.CASCADE, null=True, blank=True)
    
    # Prediction period
    prediction_month = models.DateField()
    
    # Predicted values
    predicted_amount = models.DecimalField(max_digits=15, decimal_places=2)
    confidence_interval_lower = models.DecimalField(max_digits=15, decimal_places=2)
    confidence_interval_upper = models.DecimalField(max_digits=15, decimal_places=2)
    accuracy_score = models.FloatField(default=0.0)
    
    # Model information
    model_version = models.CharField(max_length=20, default='1.0')
    feature_importance = models.JSONField(blank=True, null=True)
    
    # Actual vs Predicted (filled after the prediction period)
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    prediction_error = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_error(self, actual_value):
        """Calculate prediction error after actual value is known"""
        self.actual_amount = actual_value
        self.prediction_error = abs(self.predicted_amount - actual_value)
        self.save()
        return self.prediction_error
    
    def __str__(self):
        return f"Prediction for {self.user.username} - {self.prediction_month}"
    
    class Meta:
        db_table = 'budget_predictions'
        ordering = ['-prediction_month']
        unique_together = ['user', 'prediction_type', 'category', 'prediction_month']

class FinancialInsight(models.Model):
    """Generated financial insights and recommendations"""
    
    INSIGHT_TYPES = [
        ('spending_alert', 'Spending Alert'),
        ('savings_opportunity', 'Savings Opportunity'),
        ('budget_optimization', 'Budget Optimization'),
        ('cash_flow_warning', 'Cash Flow Warning'),
        ('goal_progress', 'Goal Progress Update'),
        ('trend_analysis', 'Trend Analysis'),
        ('comparative_analysis', 'Comparative Analysis'),
        ('seasonal_advice', 'Seasonal Advice'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='financial_insights')
    
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Priority and relevance
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    relevance_score = models.FloatField(default=0.0)  # 0-1 scale
    
    # Data and context
    insight_data = models.JSONField(blank=True, null=True)  # Supporting data
    related_categories = models.ManyToManyField('transactions.Category', blank=True)
    related_merchants = models.ManyToManyField('transactions.Merchant', blank=True)
    
    # Actionable recommendations
    recommendations = models.JSONField(blank=True, null=True)
    potential_savings = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # User interaction
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    is_acted_upon = models.BooleanField(default=False)
    user_feedback = models.CharField(
        max_length=20,
        choices=[('helpful', 'Helpful'), ('not_helpful', 'Not Helpful'), ('irrelevant', 'Irrelevant')],
        blank=True
    )
    
    # Timing
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
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
        db_table = 'financial_insights'
        ordering = ['-priority', '-relevance_score', '-generated_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'is_dismissed']),
            models.Index(fields=['insight_type', 'generated_at']),
        ]

class MonthlyFinancialSummary(models.Model):
    """Monthly financial summary and analytics"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monthly_summaries')
    
    # Period
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    
    # Income metrics
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    income_sources_count = models.PositiveIntegerField(default=0)
    primary_income_source = models.CharField(max_length=200, blank=True)
    
    # Expense metrics
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    fixed_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    variable_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    top_expense_category = models.CharField(max_length=200, blank=True)
    top_expense_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Net position
    net_income = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    savings_rate = models.FloatField(default=0.0)  # Percentage
    
    # Transaction metrics
    total_transactions = models.PositiveIntegerField(default=0)
    average_transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    most_frequent_merchant = models.CharField(max_length=200, blank=True)
    
    # Budget performance
    total_budgeted = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    budget_adherence_rate = models.FloatField(default=0.0)  # Percentage
    over_budget_categories = models.PositiveIntegerField(default=0)
    
    # Category breakdown (top 5)
    category_breakdown = models.JSONField(default=dict)
    
    # Comparisons
    income_vs_previous_month = models.FloatField(default=0.0)  # Percentage change
    expenses_vs_previous_month = models.FloatField(default=0.0)  # Percentage change
    
    # Goals progress
    active_goals_count = models.PositiveIntegerField(default=0)
    goals_on_track = models.PositiveIntegerField(default=0)
    total_goal_contributions = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # ML insights count
    insights_generated = models.PositiveIntegerField(default=0)
    high_priority_alerts = models.PositiveIntegerField(default=0)
    
    # Status
    is_finalized = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.year}-{self.month:02d}"
    
    @classmethod
    def generate_summary(cls, user, year, month):
        """Generate monthly summary for a user"""
        from transactions.models import Transaction
        from budgets.models import Budget, BudgetGoal
        from datetime import date
        
        # Get or create summary
        summary, created = cls.objects.get_or_create(
            user=user,
            year=year,
            month=month,
        )
        
        # Calculate date range
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # Get transactions for the month
        transactions = Transaction.objects.filter(
            user=user,
            transaction_date__range=[start_date, end_date]
        )
        
        # Income calculations
        income_transactions = transactions.filter(type='income')
        summary.total_income = sum(t.amount for t in income_transactions)
        summary.income_sources_count = income_transactions.values('category').distinct().count()
        
        # Expense calculations
        expense_transactions = transactions.filter(type='expense')
        summary.total_expenses = sum(t.amount for t in expense_transactions)
        
        # Net income and savings rate
        summary.net_income = summary.total_income - summary.total_expenses
        if summary.total_income > 0:
            summary.savings_rate = (summary.net_income / summary.total_income) * 100
        
        # Transaction metrics
        summary.total_transactions = transactions.count()
        if transactions.exists():
            summary.average_transaction_amount = sum(t.amount for t in transactions) / transactions.count()
        
        # Category breakdown
        category_breakdown = {}
        for transaction in expense_transactions:
            if transaction.category:
                cat_name = transaction.category.name
                category_breakdown[cat_name] = category_breakdown.get(cat_name, 0) + float(transaction.amount)
        
        # Sort and keep top 5
        sorted_categories = sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
        summary.category_breakdown = dict(sorted_categories)
        
        if sorted_categories:
            summary.top_expense_category = sorted_categories[0][0]
            summary.top_expense_amount = Decimal(str(sorted_categories[0][1]))
        
        summary.save()
        return summary
    
    class Meta:
        db_table = 'monthly_financial_summaries'
        unique_together = ['user', 'year', 'month']
        ordering = ['-year', '-month']

class TransactionCategorization(models.Model):
    """ML model data for transaction categorization"""
    
    # Training data
    description = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    merchant_name = models.CharField(max_length=200, blank=True)
    
    # Correct category (for training)
    correct_category = models.ForeignKey('transactions.Category', on_delete=models.CASCADE)
    
    # User who provided the training data
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categorization_training_data')
    
    # Model predictions (for comparison)
    predicted_category = models.ForeignKey(
        'transactions.Category',
        on_delete=models.CASCADE,
        related_name='predicted_transactions',
        null=True,
        blank=True
    )
    prediction_confidence = models.FloatField(null=True, blank=True)
    
    # Features used for classification
    extracted_features = models.JSONField(blank=True, null=True)
    
    # Status
    is_training_data = models.BooleanField(default=True)
    is_validated = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.description[:50]} -> {self.correct_category.name}"
    
    class Meta:
        db_table = 'transaction_categorizations'
        indexes = [
            models.Index(fields=['user', 'correct_category']),
            models.Index(fields=['is_training_data', 'is_validated']),
        ]

class AnalyticsConfiguration(models.Model):
    """User preferences for analytics and insights"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analytics_config')
    
    # Insight preferences
    enable_spending_alerts = models.BooleanField(default=True)
    enable_budget_recommendations = models.BooleanField(default=True)
    enable_savings_suggestions = models.BooleanField(default=True)
    enable_trend_analysis = models.BooleanField(default=True)
    enable_goal_tracking = models.BooleanField(default=True)
    
    # Alert thresholds
    spending_alert_threshold = models.FloatField(default=80.0)  # Percentage of budget
    large_transaction_threshold = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('1000.00'))
    
    # ML preferences
    enable_auto_categorization = models.BooleanField(default=True)
    auto_categorization_confidence_threshold = models.FloatField(default=0.8)
    enable_predictive_budgeting = models.BooleanField(default=True)
    
    # Notification preferences
    insight_notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Summary'),
            ('monthly', 'Monthly Report'),
        ],
        default='daily'
    )
    
    # Data retention
    keep_insights_for_days = models.PositiveIntegerField(default=90)
    keep_predictions_for_days = models.PositiveIntegerField(default=365)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics Config for {self.user.username}"
    
    class Meta:
        db_table = 'analytics_configurations'
