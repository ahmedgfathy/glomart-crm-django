from django.urls import path
from . import views

app_name = 'owner'

urlpatterns = [
    # Dashboard and main views
    path('', views.owner_dashboard, name='dashboard'),
    path('databases/', views.database_list, name='database_list'),
    path('databases/<int:database_id>/', views.database_detail, name='database_detail'),
    
    # AJAX endpoints
    path('record/<int:database_id>/<int:record_id>/', views.record_detail, name='record_detail'),
    path('sync/', views.sync_databases, name='sync_databases'),
]