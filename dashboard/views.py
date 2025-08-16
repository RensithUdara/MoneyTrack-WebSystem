from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from .models import DashboardWidget, DashboardLayout, UserPreference, Notification
from transactions.models import Transaction, Category
from budgets.models import Budget
from bank_integration.models import BankAccount
from analytics.models import FinancialInsight

def home(request):
    """Landing page"""
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    return render(request, 'dashboard/home.html')

@login_required
def dashboard(request):
    """Main dashboard view"""
    user = request.user
    
    # Get or create dashboard layout
    layout, created = DashboardLayout.objects.get_or_create(user=user)
    if created:
        # Create default widgets for new users
        create_default_widgets(user)
    
    # Get user's widgets
    widgets = DashboardWidget.objects.filter(user=user, is_visible=True).order_by('position_y', 'position_x')
    
    # Refresh widget data
    for widget in widgets:
        if not widget.last_updated or (timezone.now() - widget.last_updated).seconds > widget.refresh_interval:
            widget.refresh_data()
    
    # Get recent notifications
    notifications = Notification.objects.filter(
        user=user, 
        is_dismissed=False
    ).order_by('-created_at')[:5]
    
    # Quick stats for header
    current_month = timezone.now().replace(day=1)
    monthly_income = Transaction.objects.filter(
        user=user,
        type='income',
        transaction_date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_expenses = Transaction.objects.filter(
        user=user,
        type='expense',
        transaction_date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_balance = BankAccount.objects.filter(
        user=user,
        status='active'
    ).aggregate(total=Sum('current_balance'))['total'] or 0
    
    context = {
        'widgets': widgets,
        'layout': layout,
        'notifications': notifications,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'net_income': monthly_income - monthly_expenses,
        'total_balance': total_balance,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def summary(request):
    """Financial summary page"""
    user = request.user
    
    # Date range (default to current month)
    today = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = today.replace(day=1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = today
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get transactions for the period
    transactions = Transaction.objects.filter(
        user=user,
        transaction_date__date__range=[start_date, end_date]
    )
    
    # Calculate totals
    income_total = transactions.filter(type='income').aggregate(Sum('amount'))['total'] or 0
    expense_total = transactions.filter(type='expense').aggregate(Sum('amount'))['total'] or 0
    
    # Category breakdown
    category_expenses = transactions.filter(type='expense').values(
        'category__name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')[:10]
    
    # Monthly trend (last 12 months)
    monthly_data = []
    for i in range(12):
        month_start = (today.replace(day=1) - timedelta(days=32*i)).replace(day=1)
        if i == 11:
            month_end = month_start.replace(day=28)  # Handle February
        else:
            next_month = month_start.replace(month=month_start.month+1) if month_start.month < 12 else month_start.replace(year=month_start.year+1, month=1)
            month_end = next_month - timedelta(days=1)
        
        month_transactions = Transaction.objects.filter(
            user=user,
            transaction_date__date__range=[month_start, month_end]
        )
        
        monthly_data.append({
            'month': month_start.strftime('%B %Y'),
            'income': month_transactions.filter(type='income').aggregate(Sum('amount'))['total'] or 0,
            'expenses': month_transactions.filter(type='expense').aggregate(Sum('amount'))['total'] or 0,
        })
    
    monthly_data.reverse()  # Show oldest to newest
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'income_total': income_total,
        'expense_total': expense_total,
        'net_total': income_total - expense_total,
        'transaction_count': transactions.count(),
        'category_expenses': category_expenses,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'dashboard/summary.html', context)

@login_required
def manage_widgets(request):
    """Manage dashboard widgets"""
    if request.method == 'POST':
        # Handle widget creation/update
        widget_type = request.POST.get('widget_type')
        title = request.POST.get('title')
        size = request.POST.get('size', 'medium')
        
        widget = DashboardWidget.objects.create(
            user=request.user,
            widget_type=widget_type,
            title=title,
            size=size
        )
        
        messages.success(request, f'Widget "{title}" has been added to your dashboard.')
        return redirect('dashboard:dashboard')
    
    # Get available widget types
    available_widgets = [
        {
            'type': 'account_balance',
            'name': 'Account Balance',
            'description': 'Display current account balances'
        },
        {
            'type': 'monthly_summary',
            'name': 'Monthly Summary',
            'description': 'Monthly income and expense summary'
        },
        {
            'type': 'spending_by_category',
            'name': 'Spending by Category',
            'description': 'Pie chart of spending by category'
        },
        {
            'type': 'recent_transactions',
            'name': 'Recent Transactions',
            'description': 'List of recent transactions'
        },
        {
            'type': 'budget_status',
            'name': 'Budget Status',
            'description': 'Progress on active budgets'
        },
        {
            'type': 'financial_goals',
            'name': 'Financial Goals',
            'description': 'Progress on financial goals'
        }
    ]
    
    current_widgets = DashboardWidget.objects.filter(user=request.user)
    
    context = {
        'available_widgets': available_widgets,
        'current_widgets': current_widgets,
    }
    
    return render(request, 'dashboard/manage_widgets.html', context)

@login_required
@require_http_methods(["POST"])
def refresh_widget(request, widget_id):
    """Refresh widget data"""
    widget = get_object_or_404(DashboardWidget, id=widget_id, user=request.user)
    data = widget.refresh_data()
    
    return JsonResponse({
        'success': True,
        'data': data,
        'last_updated': widget.last_updated.isoformat() if widget.last_updated else None
    })

@login_required
@require_http_methods(["POST"])
def save_layout(request):
    """Save dashboard layout"""
    layout, created = DashboardLayout.objects.get_or_create(user=request.user)
    
    # Update layout configuration
    if 'layout_config' in request.POST:
        import json
        layout.layout_config = json.loads(request.POST['layout_config'])
        layout.save()
    
    return JsonResponse({'success': True})

@login_required
def preferences(request):
    """User preferences"""
    user = request.user
    preferences, created = UserPreference.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Update preferences
        preferences.currency_display_format = request.POST.get('currency_display_format', preferences.currency_display_format)
        preferences.date_format = request.POST.get('date_format', preferences.date_format)
        preferences.enable_push_notifications = 'enable_push_notifications' in request.POST
        preferences.enable_email_notifications = 'enable_email_notifications' in request.POST
        preferences.auto_categorize_transactions = 'auto_categorize_transactions' in request.POST
        preferences.budget_alert_percentage = int(request.POST.get('budget_alert_percentage', 80))
        preferences.save()
        
        messages.success(request, 'Your preferences have been updated.')
        return redirect('dashboard:preferences')
    
    context = {
        'preferences': preferences,
    }
    
    return render(request, 'dashboard/preferences.html', context)

@login_required
def notifications(request):
    """User notifications"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Mark as read when viewed
    unread_notifications = notifications.filter(is_read=False)
    for notification in unread_notifications:
        notification.mark_as_read()
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'dashboard/notifications.html', context)

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    return JsonResponse({'success': True})

@login_required
@require_http_methods(["POST"])
def dismiss_notification(request, notification_id):
    """Dismiss notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.dismiss()
    
    return JsonResponse({'success': True})

def create_default_widgets(user):
    """Create default widgets for new users"""
    default_widgets = [
        {
            'widget_type': 'account_balance',
            'title': 'Account Balances',
            'size': 'large',
            'position_x': 0,
            'position_y': 0,
        },
        {
            'widget_type': 'monthly_summary',
            'title': 'Monthly Summary',
            'size': 'medium',
            'position_x': 2,
            'position_y': 0,
        },
        {
            'widget_type': 'spending_by_category',
            'title': 'Spending by Category',
            'size': 'medium',
            'position_x': 0,
            'position_y': 2,
        },
        {
            'widget_type': 'recent_transactions',
            'title': 'Recent Transactions',
            'size': 'wide',
            'position_x': 2,
            'position_y': 2,
        },
    ]
    
    for widget_data in default_widgets:
        DashboardWidget.objects.create(user=user, **widget_data)
