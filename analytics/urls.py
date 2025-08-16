from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('insights/', views.InsightListView.as_view(), name='insights'),
    path('insights/<int:pk>/dismiss/', views.dismiss_insight, name='dismiss_insight'),
    path('insights/<int:pk>/feedback/', views.insight_feedback, name='insight_feedback'),
    path('reports/', views.reports_dashboard, name='reports'),
    path('reports/monthly/', views.monthly_report, name='monthly_report'),
    path('reports/category/', views.category_analysis, name='category_analysis'),
    path('reports/trends/', views.spending_trends, name='spending_trends'),
    path('predictions/', views.PredictionListView.as_view(), name='predictions'),
    path('spending-patterns/', views.spending_patterns, name='spending_patterns'),
    path('export-data/', views.export_financial_data, name='export_data'),
    path('ml-training/', views.ml_training_dashboard, name='ml_training'),
]
