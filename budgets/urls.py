from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.BudgetListView.as_view(), name='budget_list'),
    path('create/', views.BudgetCreateView.as_view(), name='create_budget'),
    path('<int:pk>/', views.BudgetDetailView.as_view(), name='budget_detail'),
    path('<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='edit_budget'),
    path('<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='delete_budget'),
    path('goals/', views.BudgetGoalListView.as_view(), name='goal_list'),
    path('goals/create/', views.BudgetGoalCreateView.as_view(), name='create_goal'),
    path('goals/<int:pk>/', views.BudgetGoalDetailView.as_view(), name='goal_detail'),
    path('goals/<int:pk>/edit/', views.BudgetGoalUpdateView.as_view(), name='edit_goal'),
    path('goals/<int:pk>/contribute/', views.ContributeToGoalView.as_view(), name='contribute_to_goal'),
    path('templates/', views.BudgetTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.BudgetTemplateCreateView.as_view(), name='create_template'),
    path('templates/<int:pk>/use/', views.use_budget_template, name='use_template'),
    path('analysis/', views.budget_analysis, name='budget_analysis'),
]
