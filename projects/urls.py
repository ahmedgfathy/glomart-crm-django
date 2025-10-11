from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Project list and CRUD operations
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<str:project_id>/', views.project_detail, name='project_detail'),
    path('<str:project_id>/edit/', views.project_edit, name='project_edit'),
    path('<str:project_id>/delete/', views.project_delete, name='project_delete'),
    
    # Import/Export
    path('export/', views.project_export, name='project_export'),
    path('import/', views.project_import, name='project_import'),
]