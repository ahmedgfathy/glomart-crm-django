from django.urls import path
from . import audit_views

app_name = 'audit'

urlpatterns = [
    path('', audit_views.audit_list, name='audit_list'),
    path('<int:audit_id>/', audit_views.audit_detail, name='audit_detail'),
    path('export/', audit_views.audit_export, name='audit_export'),
    path('api/stats/', audit_views.audit_stats_api, name='audit_stats_api'),
    path('settings/', audit_views.audit_settings, name='audit_settings'),
]