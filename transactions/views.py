from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Transaction, Category, Merchant, RecurringTransaction
import csv

class TransactionListView(LoginRequiredMixin, ListView):
    """List all transactions"""
    model = Transaction
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        
        # Apply filters
        category = self.request.GET.get('category')
        transaction_type = self.request.GET.get('type')
        search = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category__id=category)
        
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(merchant__name__icontains=search)
            )
        
        return queryset.order_by('-transaction_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            Q(user=self.request.user) | Q(is_system_default=True)
        )
        return context

class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create new transaction"""
    model = Transaction
    template_name = 'transactions/transaction_form.html'
    fields = ['type', 'amount', 'description', 'category', 'merchant', 'from_account', 'to_account', 'tags']
    success_url = reverse_lazy('transactions:transaction_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Transaction has been added successfully.')
        return super().form_valid(form)

class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Update transaction"""
    model = Transaction
    template_name = 'transactions/transaction_form.html'
    fields = ['type', 'amount', 'description', 'category', 'merchant', 'from_account', 'to_account', 'tags']
    success_url = reverse_lazy('transactions:transaction_list')
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete transaction"""
    model = Transaction
    template_name = 'transactions/transaction_confirm_delete.html'
    success_url = reverse_lazy('transactions:transaction_list')
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Transaction detail view"""
    model = Transaction
    template_name = 'transactions/transaction_detail.html'
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

class CategoryListView(LoginRequiredMixin, ListView):
    """List categories"""
    model = Category
    template_name = 'transactions/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(
            Q(user=self.request.user) | Q(is_system_default=True)
        )

class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create category"""
    model = Category
    template_name = 'transactions/category_form.html'
    fields = ['name', 'type', 'parent', 'icon', 'color', 'description']
    success_url = reverse_lazy('transactions:category_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update category"""
    model = Category
    template_name = 'transactions/category_form.html'
    fields = ['name', 'type', 'parent', 'icon', 'color', 'description']
    success_url = reverse_lazy('transactions:category_list')
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

class MerchantListView(LoginRequiredMixin, ListView):
    """List merchants"""
    model = Merchant
    template_name = 'transactions/merchant_list.html'
    context_object_name = 'merchants'
    
    def get_queryset(self):
        return Merchant.objects.filter(user=self.request.user)

class MerchantCreateView(LoginRequiredMixin, CreateView):
    """Create merchant"""
    model = Merchant
    template_name = 'transactions/merchant_form.html'
    fields = ['name', 'category', 'email', 'phone', 'website']
    success_url = reverse_lazy('transactions:merchant_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class MerchantUpdateView(LoginRequiredMixin, UpdateView):
    """Update merchant"""
    model = Merchant
    template_name = 'transactions/merchant_form.html'
    fields = ['name', 'category', 'email', 'phone', 'website']
    success_url = reverse_lazy('transactions:merchant_list')
    
    def get_queryset(self):
        return Merchant.objects.filter(user=self.request.user)

class RecurringTransactionListView(LoginRequiredMixin, ListView):
    """List recurring transactions"""
    model = RecurringTransaction
    template_name = 'transactions/recurring_list.html'
    context_object_name = 'recurring_transactions'
    
    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)

class RecurringTransactionCreateView(LoginRequiredMixin, CreateView):
    """Create recurring transaction"""
    model = RecurringTransaction
    template_name = 'transactions/recurring_form.html'
    fields = ['name', 'type', 'amount', 'description', 'category', 'merchant', 'frequency', 'start_date', 'end_date']
    success_url = reverse_lazy('transactions:recurring_transactions')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class RecurringTransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Update recurring transaction"""
    model = RecurringTransaction
    template_name = 'transactions/recurring_form.html'
    fields = ['name', 'type', 'amount', 'description', 'category', 'merchant', 'frequency', 'start_date', 'end_date']
    success_url = reverse_lazy('transactions:recurring_transactions')
    
    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)

class ImportTransactionsView(LoginRequiredMixin, DetailView):
    """Import transactions from CSV"""
    template_name = 'transactions/import_transactions.html'
    
    def post(self, request, *args, **kwargs):
        # Handle CSV upload and processing
        pass

@login_required
def export_transactions(request):
    """Export transactions to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Amount', 'Description', 'Category', 'Merchant'])
    
    transactions = Transaction.objects.filter(user=request.user).order_by('-transaction_date')
    for transaction in transactions:
        writer.writerow([
            transaction.transaction_date.strftime('%Y-%m-%d'),
            transaction.type,
            transaction.amount,
            transaction.description,
            transaction.category.name if transaction.category else '',
            transaction.merchant.name if transaction.merchant else '',
        ])
    
    return response

@login_required
def auto_categorize_transaction(request):
    """Auto-categorize transaction using ML"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        description = data.get('description', '')
        amount = data.get('amount', 0)
        
        # Simple rule-based categorization for now
        # In production, this would use ML models
        suggested_category = None
        confidence = 0.0
        
        if any(word in description.lower() for word in ['grocery', 'supermarket', 'food']):
            try:
                suggested_category = Category.objects.filter(
                    name__icontains='Food',
                    user=request.user
                ).first()
                confidence = 0.8
            except Category.DoesNotExist:
                pass
        
        return JsonResponse({
            'suggested_category_id': suggested_category.id if suggested_category else None,
            'suggested_category_name': suggested_category.name if suggested_category else None,
            'confidence': confidence
        })
    
    return JsonResponse({'error': 'Invalid request method'})
