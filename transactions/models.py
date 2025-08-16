from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class Category(models.Model):
    """Transaction categories for better organization"""
    
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    icon = models.CharField(max_length=50, blank=True)  # Font Awesome icon class
    color = models.CharField(max_length=7, default='#007bff')  # Hex color code
    description = models.TextField(blank=True)
    
    # ML categorization keywords
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for auto-categorization")
    
    # User and system categories
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    is_system_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_full_path(self):
        """Get full category path"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'
        unique_together = ['name', 'user', 'parent']
        ordering = ['type', 'name']

class Merchant(models.Model):
    """Merchant/Payee information"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='merchants')
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contact information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Merchant classification
    merchant_category_code = models.CharField(max_length=10, blank=True)  # MCC code
    business_type = models.CharField(max_length=100, blank=True)
    
    # Statistics
    total_transactions = models.PositiveIntegerField(default=0)
    total_amount_spent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    first_transaction_date = models.DateTimeField(null=True, blank=True)
    last_transaction_date = models.DateTimeField(null=True, blank=True)
    
    # Settings
    is_favorite = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'merchants'
        unique_together = ['user', 'name']
        ordering = ['name']

class Transaction(models.Model):
    """Main transaction model"""
    
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    
    # Basic transaction information
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='LKR')
    description = models.TextField()
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    merchant = models.ForeignKey(Merchant, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Account information
    from_account = models.ForeignKey('bank_integration.BankAccount', on_delete=models.CASCADE, related_name='outgoing_transactions', null=True, blank=True)
    to_account = models.ForeignKey('bank_integration.BankAccount', on_delete=models.CASCADE, related_name='incoming_transactions', null=True, blank=True)
    
    # Timing
    transaction_date = models.DateTimeField(default=timezone.now)
    value_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    # Status and processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    # Source tracking
    bank_transaction = models.ForeignKey('bank_integration.BankTransaction', on_delete=models.CASCADE, null=True, blank=True, related_name='processed_transactions')
    is_manual_entry = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False)
    
    # ML and automation
    confidence_score = models.FloatField(null=True, blank=True, help_text="ML categorization confidence (0-1)")
    is_auto_categorized = models.BooleanField(default=False)
    needs_review = models.BooleanField(default=False)
    
    # Location data
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    
    # Additional metadata
    reference_number = models.CharField(max_length=100, blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    # Shared transaction
    shared_ledger = models.ForeignKey('shared_ledger.SharedLedger', on_delete=models.CASCADE, null=True, blank=True, related_name='transactions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.type.title()} - {self.amount} {self.currency} - {self.description[:50]}"
    
    def save(self, *args, **kwargs):
        # Update merchant statistics
        if self.merchant and self.type == 'expense':
            self.merchant.total_transactions += 1
            self.merchant.total_amount_spent += self.amount
            if not self.merchant.first_transaction_date:
                self.merchant.first_transaction_date = self.transaction_date
            self.merchant.last_transaction_date = self.transaction_date
            self.merchant.save()
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'transaction_date']),
            models.Index(fields=['category', 'transaction_date']),
            models.Index(fields=['merchant', 'transaction_date']),
            models.Index(fields=['type', 'transaction_date']),
        ]

class RecurringTransaction(models.Model):
    """Template for recurring transactions"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-annual'),
        ('annual', 'Annual'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_transactions')
    
    # Template information
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=Transaction.TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='LKR')
    description = models.TextField()
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    merchant = models.ForeignKey(Merchant, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=500, blank=True)
    
    # Account information
    from_account = models.ForeignKey('bank_integration.BankAccount', on_delete=models.CASCADE, related_name='recurring_outgoing', null=True, blank=True)
    to_account = models.ForeignKey('bank_integration.BankAccount', on_delete=models.CASCADE, related_name='recurring_incoming', null=True, blank=True)
    
    # Recurrence settings
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField()
    
    # Status
    is_active = models.BooleanField(default=True)
    auto_create = models.BooleanField(default=False)
    
    # Statistics
    total_created = models.PositiveIntegerField(default=0)
    last_created_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"
    
    def create_transaction(self):
        """Create a new transaction based on this template"""
        transaction = Transaction.objects.create(
            user=self.user,
            type=self.type,
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            category=self.category,
            merchant=self.merchant,
            tags=self.tags,
            from_account=self.from_account,
            to_account=self.to_account,
            is_recurring=True,
            transaction_date=timezone.now(),
        )
        
        # Update statistics
        self.total_created += 1
        self.last_created_date = timezone.now().date()
        
        # Calculate next due date
        from dateutil.relativedelta import relativedelta
        if self.frequency == 'daily':
            self.next_due_date += relativedelta(days=1)
        elif self.frequency == 'weekly':
            self.next_due_date += relativedelta(weeks=1)
        elif self.frequency == 'bi_weekly':
            self.next_due_date += relativedelta(weeks=2)
        elif self.frequency == 'monthly':
            self.next_due_date += relativedelta(months=1)
        elif self.frequency == 'quarterly':
            self.next_due_date += relativedelta(months=3)
        elif self.frequency == 'semi_annual':
            self.next_due_date += relativedelta(months=6)
        elif self.frequency == 'annual':
            self.next_due_date += relativedelta(years=1)
        
        self.save()
        return transaction
    
    class Meta:
        db_table = 'recurring_transactions'
        ordering = ['next_due_date', 'name']

class TransactionSplit(models.Model):
    """For splitting transactions across multiple categories"""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='splits')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.transaction.id} - {self.category.name} - {self.amount}"
    
    class Meta:
        db_table = 'transaction_splits'
