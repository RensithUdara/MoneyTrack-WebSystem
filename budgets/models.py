from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta

class BudgetPeriod(models.Model):
    """Budget period definitions"""
    
    PERIOD_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-annual'),
        ('annual', 'Annual'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
    
    @classmethod
    def get_current_period(cls, period_type='monthly'):
        """Get current active budget period"""
        now = timezone.now().date()
        return cls.objects.filter(
            type=period_type,
            start_date__lte=now,
            end_date__gte=now,
            is_active=True
        ).first()
    
    class Meta:
        db_table = 'budget_periods'
        ordering = ['-start_date']

class Budget(models.Model):
    """Main budget model"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('draft', 'Draft'),
    ]
    
    ALERT_TYPES = [
        ('none', 'No Alerts'),
        ('email', 'Email Only'),
        ('sms', 'SMS Only'),
        ('both', 'Email & SMS'),
        ('push', 'Push Notifications'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Budget period
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE, related_name='budgets')
    
    # Amount settings
    total_budget_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='LKR')
    
    # Status and settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_shared = models.BooleanField(default=False)  # For family/group budgets
    
    # Alert settings
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='email')
    alert_threshold_percentage = models.IntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Send alert when spent percentage reaches this threshold"
    )
    
    # Rollover settings
    allow_rollover = models.BooleanField(default=False)
    rollover_limit_percentage = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Maximum percentage of unspent amount to rollover"
    )
    
    # Statistics (calculated fields)
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    percentage_used = models.FloatField(default=0.0)
    
    # Tracking
    last_calculated_at = models.DateTimeField(null=True, blank=True)
    alert_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.period}"
    
    def calculate_spent_amount(self):
        """Calculate total spent amount for this budget"""
        from transactions.models import Transaction
        
        spent = Decimal('0.00')
        for item in self.budget_items.all():
            # Get transactions for this budget item's category
            transactions = Transaction.objects.filter(
                user=self.user,
                category=item.category,
                type='expense',
                transaction_date__range=[self.period.start_date, self.period.end_date]
            )
            item_spent = sum(t.amount for t in transactions)
            item.spent_amount = item_spent
            item.remaining_amount = item.budgeted_amount - item_spent
            item.percentage_used = (item_spent / item.budgeted_amount * 100) if item.budgeted_amount > 0 else 0
            item.save()
            
            spent += item_spent
        
        self.total_spent = spent
        self.remaining_amount = self.total_budget_amount - spent
        self.percentage_used = (spent / self.total_budget_amount * 100) if self.total_budget_amount > 0 else 0
        self.last_calculated_at = timezone.now()
        self.save()
        
        return spent
    
    def check_alert_threshold(self):
        """Check if alert should be sent"""
        if self.percentage_used >= self.alert_threshold_percentage and not self.alert_sent_at:
            # Send alert logic here
            self.alert_sent_at = timezone.now()
            self.save()
            return True
        return False
    
    class Meta:
        db_table = 'budgets'
        ordering = ['-created_at']
        unique_together = ['user', 'name', 'period']

class BudgetItem(models.Model):
    """Individual budget line items"""
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='budget_items')
    category = models.ForeignKey('transactions.Category', on_delete=models.CASCADE, related_name='budget_items')
    
    # Budget allocation
    budgeted_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Statistics (calculated fields)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    percentage_used = models.FloatField(default=0.0)
    
    # Settings
    is_flexible = models.BooleanField(default=False, help_text="Allow overspending from other categories")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.budget.name} - {self.category.name}"
    
    @property
    def is_over_budget(self):
        return self.spent_amount > self.budgeted_amount
    
    @property
    def variance(self):
        return self.budgeted_amount - self.spent_amount
    
    class Meta:
        db_table = 'budget_items'
        unique_together = ['budget', 'category']
        ordering = ['category__name']

class BudgetGoal(models.Model):
    """Long-term budget goals"""
    
    GOAL_TYPES = [
        ('savings', 'Savings Goal'),
        ('debt_payoff', 'Debt Payoff'),
        ('investment', 'Investment Goal'),
        ('emergency_fund', 'Emergency Fund'),
        ('vacation', 'Vacation Fund'),
        ('home_purchase', 'Home Purchase'),
        ('education', 'Education Fund'),
        ('retirement', 'Retirement Savings'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budget_goals')
    
    # Goal information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    
    # Target settings
    target_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    monthly_contribution = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Timing
    start_date = models.DateField(default=timezone.now)
    target_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Account linkage
    linked_account = models.ForeignKey(
        'bank_integration.BankAccount', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Account to track goal progress"
    )
    
    # Auto-contribution settings
    auto_contribute = models.BooleanField(default=False)
    contribution_frequency = models.CharField(
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        default='monthly'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"
    
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return min((self.current_amount / self.target_amount * 100), 100)
        return 0
    
    @property
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, Decimal('0.00'))
    
    @property
    def months_remaining(self):
        if self.target_date:
            today = timezone.now().date()
            if self.target_date > today:
                return (self.target_date.year - today.year) * 12 + (self.target_date.month - today.month)
        return 0
    
    @property
    def required_monthly_contribution(self):
        months = self.months_remaining
        if months > 0:
            return self.remaining_amount / months
        return Decimal('0.00')
    
    def add_contribution(self, amount, description="Manual contribution"):
        """Add a contribution to this goal"""
        self.current_amount += amount
        if self.current_amount >= self.target_amount:
            self.status = 'completed'
            self.completion_date = timezone.now().date()
        self.save()
        
        # Create a contribution record
        BudgetGoalContribution.objects.create(
            goal=self,
            amount=amount,
            description=description
        )
    
    class Meta:
        db_table = 'budget_goals'
        ordering = ['priority', '-created_at']

class BudgetGoalContribution(models.Model):
    """Track contributions to budget goals"""
    goal = models.ForeignKey(BudgetGoal, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.CharField(max_length=200, blank=True)
    contribution_date = models.DateTimeField(default=timezone.now)
    
    # Link to transaction if applicable
    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='goal_contribution'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.goal.name} - {self.amount} on {self.contribution_date.date()}"
    
    class Meta:
        db_table = 'budget_goal_contributions'
        ordering = ['-contribution_date']

class BudgetTemplate(models.Model):
    """Reusable budget templates"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budget_templates')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template settings
    is_public = models.BooleanField(default=False)
    is_system_template = models.BooleanField(default=False)
    
    # Usage statistics
    times_used = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def create_budget_from_template(self, user, period, total_amount):
        """Create a new budget based on this template"""
        budget = Budget.objects.create(
            user=user,
            name=f"{self.name} - {period}",
            period=period,
            total_budget_amount=total_amount,
        )
        
        # Create budget items based on template items
        for template_item in self.template_items.all():
            allocation_amount = (template_item.percentage / 100) * total_amount
            BudgetItem.objects.create(
                budget=budget,
                category=template_item.category,
                budgeted_amount=allocation_amount,
                notes=template_item.notes,
            )
        
        self.times_used += 1
        self.save()
        
        return budget
    
    class Meta:
        db_table = 'budget_templates'
        ordering = ['-times_used', 'name']

class BudgetTemplateItem(models.Model):
    """Items in budget templates"""
    template = models.ForeignKey(BudgetTemplate, on_delete=models.CASCADE, related_name='template_items')
    category = models.ForeignKey('transactions.Category', on_delete=models.CASCADE)
    percentage = models.FloatField(validators=[MinValueValidator(0.1), MaxValueValidator(100)])
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.template.name} - {self.category.name} ({self.percentage}%)"
    
    class Meta:
        db_table = 'budget_template_items'
        unique_together = ['template', 'category']
