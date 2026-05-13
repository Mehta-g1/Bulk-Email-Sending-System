from django.urls import path
from . import views

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('<int:campaign_id>/progress/', views.campaign_progress, name='campaign_progress'),
    path('<int:campaign_id>/logs/', views.campaign_logs, name='campaign_logs'),
    path('<int:campaign_id>/export-csv/', views.export_campaign_csv, name='export_campaign_csv'),
]
