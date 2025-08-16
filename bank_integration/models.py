from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from cryptography.fernet import Fernet
from django.utils import timezone
import json

class Bank(models.Model):
    """Bank information model"""
    
    BANK_CHOICES = [
        ('NSB', 'National Savings Bank'),
        ('PEOPLES', 'Peoples Bank'),
        ('SAMPATH', 'Sampath Bank'),
        ('COMMERCIAL', 'Commercial Bank'),
        ('BOC', 'Bank of Ceylon'),
        ('HNB', 'Hatton National Bank'),
        ('DFCC', 'DFCC Bank'),
        ('NDB', 'National Development Bank'),
        ('SEYLAN', 'Seylan Bank'),
        ('UNION', 'Union Bank'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, choices=BANK_CHOICES, unique=True)
    api_endpoint = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='bank_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    supports_api_integration = models.BooleanField(default=False)
    
    # API Configuration
    api_version = models.CharField(max_length=10, blank=True)
    api_documentation_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'banks'
        ordering = ['name']

class BankAccount(models.Model):
    """User's bank account information"""
    
    ACCOUNT_TYPES = [
        ('savings', 'Savings Account'),
        ('current', 'Current Account'),
        ('fixed', 'Fixed Deposit'),
        ('credit', 'Credit Card'),
        ('loan', 'Loan Account'),
        ('investment', 'Investment Account'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts')
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    currency = models.CharField(max_length=3, default='LKR')
    
    # Balance information
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_updated = models.DateTimeField(default=timezone.now)
    
    # API Integration
    is_api_connected = models.BooleanField(default=False)
    encrypted_credentials = models.TextField(blank=True)  # Encrypted API credentials
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_frequency = models.IntegerField(default=300)  # seconds
    
    # Account status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_primary = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    
    # Metadata
    branch_code = models.CharField(max_length=20, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.bank.name} - {self.account_number[-4:].rjust(4, '*')}"
    
    def encrypt_credentials(self, credentials_dict):
        """Encrypt API credentials"""
        key = Fernet.generate_key()
        f = Fernet(key)
        encrypted_data = f.encrypt(json.dumps(credentials_dict).encode())
        self.encrypted_credentials = encrypted_data.decode()
        # Store key securely (in production, use environment variables or key management service)
        return key
    
    def decrypt_credentials(self, key):
        """Decrypt API credentials"""
        if not self.encrypted_credentials:
            return {}
        f = Fernet(key)
        decrypted_data = f.decrypt(self.encrypted_credentials.encode())
        return json.loads(decrypted_data.decode())
    
    class Meta:
        db_table = 'bank_accounts'
        unique_together = ['user', 'bank', 'account_number']
        ordering = ['-is_primary', 'bank__name']

class BankTransaction(models.Model):
    """Raw bank transaction data from API"""
    
    TRANSACTION_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]
    
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='raw_transactions')
    
    # Transaction identifiers
    transaction_id = models.CharField(max_length=100)  # Bank's transaction ID
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Transaction details
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='LKR')
    description = models.TextField()
    
    # Timing
    transaction_date = models.DateTimeField()
    value_date = models.DateField()
    
    # Balance information
    balance_after = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Additional details
    merchant_name = models.CharField(max_length=200, blank=True)
    merchant_category = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.account} - {self.transaction_type} {self.amount} on {self.transaction_date}"
    
    class Meta:
        db_table = 'bank_transactions'
        unique_together = ['account', 'transaction_id']
        ordering = ['-transaction_date']

class APILog(models.Model):
    """Log API calls for monitoring and debugging"""
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
        ('rate_limited', 'Rate Limited'),
    ]
    
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='api_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    endpoint = models.URLField()
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    request_data = models.JSONField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    
    response_time = models.FloatField()  # in seconds
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bank.code} API - {self.status} at {self.timestamp}"
    
    class Meta:
        db_table = 'api_logs'
        ordering = ['-timestamp']
