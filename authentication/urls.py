from django.urls import path
from . import views
from . import user_settings

app_name = 'authentication'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Settings
    path('settings/profile/', user_settings.user_profile_settings, name='user_profile_settings'),
    path('settings/company/', user_settings.company_settings, name='company_settings'),
    
    # User Management
    path('users/', views.user_management_view, name='users'),
    path('users/create/', views.create_user_view, name='create_user'),
    path('users/<int:user_id>/', views.view_user_profile, name='view_user_profile'),
    path('users/<int:user_id>/edit/', views.edit_user_view, name='edit_user'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
    path('users/<int:user_id>/assign-profile/', views.assign_user_profile_view, name='assign_profile'),
    
    # Profile Management
    path('profiles/', views.profiles_view, name='profiles'),
    path('profiles/create/', views.create_profile_view, name='create_profile'),
    path('profiles/<int:profile_id>/', views.profile_detail_view, name='profile_detail'),
    path('profiles/<int:profile_id>/edit/', views.edit_profile_view, name='edit_profile'),
    path('profiles/<int:profile_id>/delete/', views.delete_profile_view, name='delete_profile'),
    path('profiles/<int:profile_id>/permissions/', views.update_profile_permissions, name='update_permissions'),
    path('profiles/<int:profile_id>/fields/<str:module_name>/', views.get_module_fields, name='get_module_fields'),
    path('profiles/<int:profile_id>/data-filters/', views.manage_data_filter, name='manage_data_filter'),
    path('profiles/<int:profile_id>/dropdown-restrictions/', views.manage_dropdown_restriction, name='manage_dropdown_restriction'),
    path('model-fields/<str:module_name>/', views.get_model_fields_for_filter, name='get_model_fields_for_filter'),
    path('field-choices/<str:module_name>/<path:field_name>/', views.get_field_choices, name='get_field_choices'),
    path('auth-check/', views.auth_check_view, name='auth_check'),
]