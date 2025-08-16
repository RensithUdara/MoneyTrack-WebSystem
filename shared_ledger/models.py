from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class SharedLedger(models.Model):
    """Collaborative ledger for shared expenses"""
    
    LEDGER_TYPES = [
        ('family', 'Family'),
        ('roommates', 'Roommates'),
        ('friends', 'Friends'),
        ('business', 'Business Partners'),
        ('travel', 'Travel Group'),
        ('project', 'Project Team'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
        ('closed', 'Closed'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ledger_type = models.CharField(max_length=20, choices=LEDGER_TYPES)
    
    # Creator and management
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_ledgers')
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='admin_ledgers', blank=True)
    
    # Settings
    currency = models.CharField(max_length=3, default='LKR')
    is_public = models.BooleanField(default=False)
    require_approval = models.BooleanField(default=False)
    allow_file_uploads = models.BooleanField(default=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Statistics
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_members = models.PositiveIntegerField(default=0)
    
    # Invite settings
    invite_code = models.CharField(max_length=20, unique=True, blank=True)
    invite_expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def generate_invite_code(self):
        """Generate a unique invite code"""
        import random
        import string
        
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        while SharedLedger.objects.filter(invite_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        self.invite_code = code
        self.invite_expires_at = timezone.now() + timezone.timedelta(days=7)
        self.save()
        return code
    
    def calculate_balances(self):
        """Calculate member balances"""
        balances = {}
        
        for member in self.members.all():
            total_paid = sum(
                expense.amount for expense in self.expenses.filter(paid_by=member.user)
            )
            
            total_share = Decimal('0.00')
            for expense in self.expenses.all():
                member_share = expense.splits.filter(member=member).first()
                if member_share:
                    total_share += member_share.amount
            
            balances[member.user.id] = {
                'user': member.user,
                'total_paid': total_paid,
                'total_share': total_share,
                'balance': total_paid - total_share,
            }
        
        return balances
    
    class Meta:
        db_table = 'shared_ledgers'
        ordering = ['-created_at']

class SharedLedgerMember(models.Model):
    """Members of a shared ledger"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('invited', 'Invited'),
        ('inactive', 'Inactive'),
        ('removed', 'Removed'),
    ]
    
    ledger = models.ForeignKey(SharedLedger, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_memberships')
    
    # Member settings
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Notification settings
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Join information
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_members'
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(default=timezone.now)
    
    # Personal settings
    display_name = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color for charts
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} in {self.ledger.name}"
    
    @property
    def name(self):
        return self.display_name or self.user.get_full_name() or self.user.username
    
    class Meta:
        db_table = 'shared_ledger_members'
        unique_together = ['ledger', 'user']
        ordering = ['joined_at']

class SharedExpense(models.Model):
    """Shared expenses within a ledger"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('settled', 'Settled'),
    ]
    
    SPLIT_METHODS = [
        ('equal', 'Split Equally'),
        ('exact', 'Exact Amounts'),
        ('percentage', 'By Percentage'),
        ('shares', 'By Shares'),
    ]
    
    ledger = models.ForeignKey(SharedLedger, on_delete=models.CASCADE, related_name='expenses')
    
    # Basic expense information
    description = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='LKR')
    
    # Who paid
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='paid_expenses')
    
    # Categorization
    category = models.ForeignKey('transactions.Category', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=500, blank=True)
    
    # Timing
    expense_date = models.DateTimeField(default=timezone.now)
    
    # Splitting
    split_method = models.CharField(max_length=20, choices=SPLIT_METHODS, default='equal')
    
    # Status and approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_expenses')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Files and receipts
    receipt_image = models.ImageField(upload_to='shared_receipts/', blank=True, null=True)
    attachment = models.FileField(upload_to='shared_attachments/', blank=True, null=True)
    
    # Location (optional)
    location_name = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Notes and comments
    notes = models.TextField(blank=True)
    
    # Linked transaction (if synchronized with personal transactions)
    linked_transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shared_expense'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency}"
    
    def create_equal_splits(self):
        """Create equal splits for all active members"""
        active_members = self.ledger.members.filter(status='active')
        amount_per_person = self.amount / active_members.count()
        
        for member in active_members:
            SharedExpenseSplit.objects.get_or_create(
                expense=self,
                member=member,
                defaults={
                    'amount': amount_per_person,
                    'percentage': 100 / active_members.count(),
                    'shares': 1,
                }
            )
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Auto-create equal splits for new expenses
        if is_new and self.split_method == 'equal':
            self.create_equal_splits()
    
    class Meta:
        db_table = 'shared_expenses'
        ordering = ['-expense_date', '-created_at']

class SharedExpenseSplit(models.Model):
    """How expenses are split among members"""
    expense = models.ForeignKey(SharedExpense, on_delete=models.CASCADE, related_name='splits')
    member = models.ForeignKey(SharedLedgerMember, on_delete=models.CASCADE, related_name='expense_splits')
    
    # Split details
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    shares = models.PositiveIntegerField(default=1)
    
    # Payment status
    is_settled = models.BooleanField(default=False)
    settled_at = models.DateTimeField(null=True, blank=True)
    settlement_method = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.member.name} owes {self.amount} for {self.expense.description}"
    
    def settle(self, method=""):
        """Mark this split as settled"""
        self.is_settled = True
        self.settled_at = timezone.now()
        self.settlement_method = method
        self.save()
    
    class Meta:
        db_table = 'shared_expense_splits'
        unique_together = ['expense', 'member']

class SharedPayment(models.Model):
    """Payments between ledger members"""
    ledger = models.ForeignKey(SharedLedger, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    from_member = models.ForeignKey(SharedLedgerMember, on_delete=models.CASCADE, related_name='payments_made')
    to_member = models.ForeignKey(SharedLedgerMember, on_delete=models.CASCADE, related_name='payments_received')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='LKR')
    
    # Payment information
    description = models.CharField(max_length=200, default="Settlement payment")
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Status
    is_confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_payments'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Related expenses (for partial settlements)
    related_splits = models.ManyToManyField(SharedExpenseSplit, blank=True, related_name='settlement_payments')
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.from_member.name} → {self.to_member.name}: {self.amount} {self.currency}"
    
    def confirm_payment(self, confirmed_by_user):
        """Confirm this payment"""
        self.is_confirmed = True
        self.confirmed_by = confirmed_by_user
        self.confirmed_at = timezone.now()
        self.save()
        
        # Mark related splits as settled
        for split in self.related_splits.all():
            split.settle(method=self.payment_method)
    
    class Meta:
        db_table = 'shared_payments'
        ordering = ['-payment_date']

class SharedLedgerInvite(models.Model):
    """Invitations to join shared ledgers"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    ledger = models.ForeignKey(SharedLedger, on_delete=models.CASCADE, related_name='invites')
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invites')
    
    # Invitee information
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_invites'
    )
    
    # Invite details
    message = models.TextField(blank=True)
    proposed_role = models.CharField(max_length=20, choices=SharedLedgerMember.ROLE_CHOICES, default='member')
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invite to {self.ledger.name} for {self.email}"
    
    def accept(self, user):
        """Accept the invitation"""
        if self.status == 'pending' and timezone.now() <= self.expires_at:
            self.status = 'accepted'
            self.invited_user = user
            self.responded_at = timezone.now()
            self.save()
            
            # Create membership
            SharedLedgerMember.objects.create(
                ledger=self.ledger,
                user=user,
                role=self.proposed_role,
                invited_by=self.invited_by,
                invited_at=self.created_at,
            )
            
            return True
        return False
    
    def decline(self):
        """Decline the invitation"""
        if self.status == 'pending':
            self.status = 'declined'
            self.responded_at = timezone.now()
            self.save()
            return True
        return False
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    class Meta:
        db_table = 'shared_ledger_invites'
        ordering = ['-created_at']

class SharedLedgerActivity(models.Model):
    """Activity log for shared ledgers"""
    
    ACTIVITY_TYPES = [
        ('member_joined', 'Member Joined'),
        ('member_left', 'Member Left'),
        ('expense_added', 'Expense Added'),
        ('expense_updated', 'Expense Updated'),
        ('expense_deleted', 'Expense Deleted'),
        ('payment_made', 'Payment Made'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('settlement_completed', 'Settlement Completed'),
        ('ledger_updated', 'Ledger Updated'),
    ]
    
    ledger = models.ForeignKey(SharedLedger, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ledger_activities')
    
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    # Optional references
    related_expense = models.ForeignKey(SharedExpense, on_delete=models.SET_NULL, null=True, blank=True)
    related_payment = models.ForeignKey(SharedPayment, on_delete=models.SET_NULL, null=True, blank=True)
    related_member = models.ForeignKey(SharedLedgerMember, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} {self.description} in {self.ledger.name}"
    
    class Meta:
        db_table = 'shared_ledger_activities'
        ordering = ['-created_at']
