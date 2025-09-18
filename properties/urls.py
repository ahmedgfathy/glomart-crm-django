from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    # Property list and search
    path('', views.property_list, name='property_list'),
    path('search/', views.property_search, name='property_search'),
    
    # Property CRUD
    path('create/', views.property_create, name='property_create'),
    path('<str:property_id>/', views.property_detail, name='property_detail'),
    path('<str:property_id>/edit/', views.property_edit, name='property_edit'),
    path('<str:property_id>/delete/', views.property_delete, name='property_delete'),
    
    # Property actions
    path('<str:property_id>/like/', views.property_like, name='property_like'),
    path('<str:property_id>/assign/', views.property_assign, name='property_assign'),
    
    # Export functionality
    path('export/', views.property_export, name='property_export'),
    
    # Import functionality
    path('import/', views.property_import, name='property_import'),
    
    # API endpoints for dynamic loading
    path('api/regions/', views.api_regions, name='api_regions'),
    path('api/compounds/', views.api_compounds, name='api_compounds'),
    path('api/save-view-preference/', views.save_view_preference, name='save_view_preference'),
    path('<str:property_id>/images/', views.property_images_api, name='property_images_api'),
]