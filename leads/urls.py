from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    # Dashboard and main views
    path('', views.leads_list_view, name='leads_list'),
    path('dashboard/', views.leads_dashboard_view, name='dashboard'),
    
    # Lead CRUD operations
    path('create/', views.lead_create_view, name='create_lead'),
    path('<uuid:lead_id>/', views.lead_detail_view, name='lead_detail'),
    path('<uuid:lead_id>/edit/', views.lead_edit_view, name='edit_lead'),
    path('<uuid:lead_id>/delete/', views.lead_delete_view, name='delete_lead'),
    
    # Lead management actions
    path('<uuid:lead_id>/convert/', views.lead_convert_view, name='convert_lead'),
    path('<uuid:lead_id>/assign/', views.lead_assign_view, name='assign_lead'),
    path('<uuid:lead_id>/score/', views.update_lead_score_view, name='update_score'),
    
    # Notes and activities
    path('<uuid:lead_id>/notes/', views.lead_notes_view, name='lead_notes'),
    path('<uuid:lead_id>/notes/add/', views.add_lead_note_view, name='add_note'),
    path('notes/<int:note_id>/delete/', views.delete_lead_note_view, name='delete_note'),
    
    # Activities
    path('<uuid:lead_id>/activities/', views.lead_activities_view, name='lead_activities'),
    path('<uuid:lead_id>/activities/add/', views.add_lead_activity_view, name='add_activity'),
    path('activities/<int:activity_id>/complete/', views.complete_activity_view, name='complete_activity'),
    path('activities/<int:activity_id>/delete/', views.delete_activity_view, name='delete_activity'),
    
    # Bulk operations
    path('bulk/assign/', views.bulk_assign_leads_view, name='bulk_assign'),
    path('bulk/delete/', views.bulk_delete_leads_view, name='bulk_delete'),
    path('bulk/export/', views.export_leads_view, name='export_leads'),
    path('bulk/import/', views.import_leads_view, name='import_leads'),
    
    # API endpoints for AJAX
    path('api/update-status/', views.update_lead_status_api, name='update_status_api'),
    path('api/quick-note/', views.add_quick_note_api, name='quick_note_api'),
    path('api/archive/', views.archive_lead_api, name='archive_lead_api'),
    path('api/search/', views.leads_search_api, name='search_api'),
    path('api/save-column-preferences/', views.save_column_preferences, name='save_column_preferences'),
    
    # Source and status management
    path('sources/', views.lead_sources_view, name='sources'),
    path('sources/create/', views.create_lead_source_view, name='create_source'),
    path('statuses/', views.lead_statuses_view, name='statuses'),
    path('statuses/create/', views.create_lead_status_view, name='create_status'),
]