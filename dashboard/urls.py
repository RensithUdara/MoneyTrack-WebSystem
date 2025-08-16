from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('summary/', views.summary, name='summary'),
    path('widgets/', views.manage_widgets, name='manage_widgets'),
    path('widget/<int:widget_id>/refresh/', views.refresh_widget, name='refresh_widget'),
    path('layout/', views.save_layout, name='save_layout'),
    path('preferences/', views.preferences, name='preferences'),
    path('notifications/', views.notifications, name='notifications'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notification/<int:notification_id>/dismiss/', views.dismiss_notification, name='dismiss_notification'),
]
