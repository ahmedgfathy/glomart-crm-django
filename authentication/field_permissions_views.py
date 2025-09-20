from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from authentication.models import (
    Module, Profile, FieldPermission, DataFilter, DynamicDropdown, 
    ProfileDataScope
)
from django.core.paginator import Paginator
import json

def is_admin_or_manager(user):
    """Check if user is admin or has manager profile"""
    return user.is_superuser or (hasattr(user, 'user_profile') and 
                                user.user_profile.profile and 
                                'manager' in user.user_profile.profile.name.lower())

@login_required
@user_passes_test(is_admin_or_manager)
def field_permissions_dashboard(request):
    """Main dashboard for field permissions management"""
    
    # Get overview statistics
    total_permissions = FieldPermission.objects.count()
    active_permissions = FieldPermission.objects.filter(is_active=True).count()
    profiles_count = Profile.objects.filter(is_active=True).count()
    modules_count = Module.objects.filter(is_active=True).count()
    
    # Get permissions by profile
    profile_stats = []
    for profile in Profile.objects.filter(is_active=True):
        stats = {
            'profile': profile,
            'total_fields': FieldPermission.objects.filter(profile=profile).count(),
            'viewable_fields': FieldPermission.objects.filter(profile=profile, can_view=True).count(),
            'editable_fields': FieldPermission.objects.filter(profile=profile, can_edit=True).count(),
            'data_filters': DataFilter.objects.filter(profile=profile, is_active=True).count(),
            'dropdown_restrictions': DynamicDropdown.objects.filter(profile=profile, is_active=True).count(),
        }
        profile_stats.append(stats)
    
    # Get recent changes (if you have audit logs)
    recent_changes = []  # You can implement this based on your audit system
    
    context = {
        'total_permissions': total_permissions,
        'active_permissions': active_permissions,
        'profiles_count': profiles_count,
        'modules_count': modules_count,
        'profile_stats': profile_stats,
        'recent_changes': recent_changes,
    }
    
    return render(request, 'authentication/field_permissions_dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def field_permissions_matrix(request):
    """Matrix view of all field permissions"""
    
    # Get all active profiles
    profiles = Profile.objects.filter(is_active=True)
    
    # Get all active modules
    modules = Module.objects.filter(is_active=True)
    
    # Prepare field data organized by module
    field_data = {}
    
    for module in modules:
        # Get all field permissions for this module
        module_permissions = FieldPermission.objects.filter(
            module=module,
            is_active=True
        ).select_related('profile').order_by('model_name', 'field_name')
        
        # Group permissions by field
        fields_dict = {}
        for permission in module_permissions:
            field_key = f"{permission.model_name}.{permission.field_name}"
            
            if field_key not in fields_dict:
                fields_dict[field_key] = {
                    'name': permission.field_name,
                    'verbose_name': permission.field_name.replace('_', ' ').title(),
                    'model_name': permission.model_name,
                    'type': 'text',  # Default type since field_type doesn't exist
                    'required': False,  # Default since is_required doesn't exist
                    'help_text': '',  # Default since help_text doesn't exist
                    'permissions': {}
                }
            
            # Store permissions for this field by profile
            fields_dict[field_key]['permissions'][permission.profile.id] = {
                'can_view': permission.can_view,
                'can_edit': permission.can_edit,
                'is_visible_in_list': permission.is_visible_in_list,
                'is_visible_in_detail': permission.is_visible_in_detail,
                'is_visible_in_forms': permission.is_visible_in_forms,
            }
        
        if fields_dict:
            field_data[module.name] = list(fields_dict.values())
    
    # Calculate columns count for template
    columns_count = (len(profiles) * 2) + 1  # 2 columns per profile (view/edit) + 1 for field name
    
    context = {
        'profiles': profiles,
        'modules': modules,
        'field_data': field_data,
        'columns_count': columns_count,
    }
    
    return render(request, 'authentication/field_permissions_matrix.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def profile_field_editor(request, profile_id):
    """Edit all field permissions for a specific profile"""
    
    profile = get_object_or_404(Profile, id=profile_id, is_active=True)
    
    if request.method == 'POST':
        # Process bulk field permission updates
        updated_count = 0
        
        for key, value in request.POST.items():
            if key.startswith('field_'):
                # Parse field permission updates
                # Format: field_{permission_id}_{permission_type}
                parts = key.split('_')
                if len(parts) >= 3:
                    permission_id = parts[1]
                    permission_type = parts[2]
                    
                    try:
                        permission = FieldPermission.objects.get(id=permission_id, profile=profile)
                        
                        if permission_type == 'view':
                            permission.can_view = value == 'on'
                        elif permission_type == 'edit':
                            permission.can_edit = value == 'on'
                        elif permission_type == 'list':
                            permission.is_visible_in_list = value == 'on'
                        elif permission_type == 'detail':
                            permission.is_visible_in_detail = value == 'on'
                        elif permission_type == 'forms':
                            permission.is_visible_in_forms = value == 'on'
                        
                        permission.save()
                        updated_count += 1
                        
                    except FieldPermission.DoesNotExist:
                        continue
        
        messages.success(request, f'Updated {updated_count} field permissions for {profile.name}')
        return redirect('authentication:profile_field_editor', profile_id=profile_id)
    
    # Get all field permissions for this profile, organized by module
    modules_data = []
    for module in Module.objects.filter(is_active=True):
        permissions = FieldPermission.objects.filter(
            profile=profile, 
            module=module
        ).order_by('model_name', 'field_name')
        
        if permissions.exists():
            # Group by model
            models_data = {}
            for permission in permissions:
                if permission.model_name not in models_data:
                    models_data[permission.model_name] = []
                models_data[permission.model_name].append(permission)
            
            modules_data.append({
                'module': module,
                'models': models_data,
                'total_fields': permissions.count(),
                'viewable_fields': permissions.filter(can_view=True).count(),
            })
    
    context = {
        'profile': profile,
        'modules_data': modules_data,
    }
    
    return render(request, 'authentication/profile_field_editor.html', context)

@require_POST
@login_required
@user_passes_test(is_admin_or_manager)
def bulk_update_permissions(request):
    """AJAX endpoint for bulk permission updates from matrix view"""
    
    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])
        
        updated_count = 0
        
        for change in changes:
            profile_id = change.get('profile_id')
            field_name = change.get('field_name')
            module = change.get('module')
            permission_type = change.get('permission_type')
            value = change.get('value')
            
            try:
                # Find the corresponding field permission
                permission = FieldPermission.objects.get(
                    profile_id=profile_id,
                    field_name=field_name,
                    module__name=module
                )
                
                # Update the specific permission
                if permission_type == 'view':
                    permission.can_view = value
                elif permission_type == 'edit':
                    permission.can_edit = value
                    # Auto-enable view if edit is enabled
                    if value:
                        permission.can_view = True
                elif permission_type == 'list':
                    permission.is_visible_in_list = value
                elif permission_type == 'detail':
                    permission.is_visible_in_detail = value
                elif permission_type == 'forms':
                    permission.is_visible_in_forms = value
                
                permission.save()
                updated_count += 1
                
            except FieldPermission.DoesNotExist:
                # Create new permission if it doesn't exist
                try:
                    module_obj = Module.objects.get(name=module)
                    profile_obj = Profile.objects.get(id=profile_id)
                    
                    permission_data = {
                        'profile': profile_obj,
                        'module': module_obj,
                        'field_name': field_name,
                        'can_view': permission_type == 'view' and value,
                        'can_edit': permission_type == 'edit' and value,
                        'is_visible_in_list': permission_type == 'list' and value,
                        'is_visible_in_detail': permission_type == 'detail' and value,
                        'is_visible_in_forms': permission_type == 'forms' and value,
                        'is_active': True
                    }
                    
                    # Auto-enable view if edit is enabled
                    if permission_type == 'edit' and value:
                        permission_data['can_view'] = True
                    
                    FieldPermission.objects.create(**permission_data)
                    updated_count += 1
                    
                except (Module.DoesNotExist, Profile.DoesNotExist):
                    continue
        
        return JsonResponse({
            'success': True,
            'message': f'Updated {updated_count} permissions',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@user_passes_test(is_admin_or_manager)
def data_filters_manager(request):
    """Manage data filters for profiles"""
    
    profile_id = request.GET.get('profile')
    
    filters = DataFilter.objects.select_related('profile', 'module').all()
    if profile_id:
        filters = filters.filter(profile_id=profile_id)
    
    profiles = Profile.objects.filter(is_active=True)
    modules = Module.objects.filter(is_active=True)
    
    context = {
        'filters': filters,
        'profiles': profiles,
        'modules': modules,
        'selected_profile': profile_id,
    }
    
    return render(request, 'authentication/data_filters_manager.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def edit_data_filter(request, filter_id):
    """Edit a specific data filter"""
    data_filter = get_object_or_404(DataFilter, id=filter_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update filter fields
            data_filter.name = data.get('name', data_filter.name)
            data_filter.description = data.get('description', data_filter.description)
            data_filter.model_name = data.get('model_name', data_filter.model_name)
            data_filter.filter_type = data.get('filter_type', data_filter.filter_type)
            data_filter.filter_conditions = data.get('filter_conditions', data_filter.filter_conditions)
            data_filter.is_active = data.get('is_active', data_filter.is_active)
            
            # Update profile if provided
            profile_id = data.get('profile_id')
            if profile_id:
                data_filter.profile_id = profile_id
            
            # Update module if provided
            module_id = data.get('module_id')
            if module_id:
                data_filter.module_id = module_id
                
            data_filter.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Data filter updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating filter: {str(e)}'
            })
    
    # GET request - return filter data for editing
    return JsonResponse({
        'id': data_filter.id,
        'name': data_filter.name,
        'description': data_filter.description,
        'model_name': data_filter.model_name,
        'filter_type': data_filter.filter_type,
        'filter_conditions': data_filter.filter_conditions,
        'is_active': data_filter.is_active,
        'profile_id': data_filter.profile_id,
        'profile_name': data_filter.profile.name if data_filter.profile else '',
        'module_id': data_filter.module_id,
        'module_name': data_filter.module.name if data_filter.module else ''
    })

@login_required
@user_passes_test(is_admin_or_manager)
def delete_data_filter(request, filter_id):
    """Delete a specific data filter"""
    if request.method == 'POST':
        try:
            data_filter = get_object_or_404(DataFilter, id=filter_id)
            filter_name = f"{data_filter.name} ({data_filter.profile.name if data_filter.profile else 'No Profile'})"
            data_filter.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Data filter "{filter_name}" deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting filter: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin_or_manager)
def create_data_filter(request):
    """Create a new data filter"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create new filter
            data_filter = DataFilter.objects.create(
                profile_id=data.get('profile_id'),
                module_id=data.get('module_id'),
                name=data.get('name'),
                description=data.get('description', ''),
                model_name=data.get('model_name'),
                filter_type=data.get('filter_type', 'include'),
                filter_conditions=data.get('filter_conditions', {}),
                is_active=data.get('is_active', True)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Data filter created successfully',
                'filter_id': data_filter.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating filter: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin_or_manager)
def dropdown_restrictions_manager(request):
    """Manage dropdown restrictions for profiles"""
    
    profile_id = request.GET.get('profile')
    
    dropdowns = DynamicDropdown.objects.select_related('profile', 'module').all()
    if profile_id:
        dropdowns = dropdowns.filter(profile_id=profile_id)
    
    profiles = Profile.objects.filter(is_active=True)
    modules = Module.objects.filter(is_active=True)
    
    context = {
        'dropdowns': dropdowns,
        'profiles': profiles,
        'modules': modules,
        'selected_profile': profile_id,
    }
    
    return render(request, 'authentication/dropdown_restrictions_manager.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def edit_dropdown_restriction(request, restriction_id):
    """Edit a specific dropdown restriction"""
    dropdown = get_object_or_404(DynamicDropdown, id=restriction_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update dropdown fields
            dropdown.name = data.get('name', dropdown.name)
            dropdown.field_name = data.get('field_name', dropdown.field_name)
            dropdown.source_model = data.get('source_model', dropdown.source_model)
            dropdown.source_field = data.get('source_field', dropdown.source_field)
            dropdown.display_field = data.get('display_field', dropdown.display_field)
            dropdown.allowed_values = data.get('allowed_values', dropdown.allowed_values)
            dropdown.restricted_values = data.get('restricted_values', dropdown.restricted_values)
            dropdown.filter_conditions = data.get('filter_conditions', dropdown.filter_conditions)
            dropdown.is_active = data.get('is_active', dropdown.is_active)
            
            # Update profile if provided
            profile_id = data.get('profile_id')
            if profile_id:
                dropdown.profile_id = profile_id
            
            # Update module if provided
            module_id = data.get('module_id')
            if module_id:
                dropdown.module_id = module_id
                
            dropdown.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Dropdown restriction updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating restriction: {str(e)}'
            })
    
    # GET request - return dropdown data for editing
    return JsonResponse({
        'id': dropdown.id,
        'name': dropdown.name,
        'field_name': dropdown.field_name,
        'source_model': dropdown.source_model,
        'source_field': dropdown.source_field,
        'display_field': dropdown.display_field,
        'allowed_values': dropdown.allowed_values,
        'restricted_values': dropdown.restricted_values,
        'filter_conditions': dropdown.filter_conditions,
        'is_active': dropdown.is_active,
        'profile_id': dropdown.profile_id,
        'profile_name': dropdown.profile.name if dropdown.profile else '',
        'module_id': dropdown.module_id,
        'module_name': dropdown.module.name if dropdown.module else ''
    })

@login_required
@user_passes_test(is_admin_or_manager)
def delete_dropdown_restriction(request, restriction_id):
    """Delete a specific dropdown restriction"""
    if request.method == 'POST':
        try:
            dropdown = get_object_or_404(DynamicDropdown, id=restriction_id)
            restriction_name = f"{dropdown.field_name} ({dropdown.profile.name if dropdown.profile else 'No Profile'})"
            dropdown.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Dropdown restriction "{restriction_name}" deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting restriction: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin_or_manager)
def create_dropdown_restriction(request):
    """Create a new dropdown restriction"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create new dropdown restriction
            dropdown = DynamicDropdown.objects.create(
                profile_id=data.get('profile_id'),
                module_id=data.get('module_id'),
                name=data.get('name'),
                field_name=data.get('field_name'),
                source_model=data.get('source_model', ''),
                source_field=data.get('source_field', ''),
                display_field=data.get('display_field', ''),
                allowed_values=data.get('allowed_values', []),
                restricted_values=data.get('restricted_values', []),
                filter_conditions=data.get('filter_conditions', {}),
                is_active=data.get('is_active', True)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Dropdown restriction created successfully',
                'restriction_id': dropdown.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating restriction: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@require_POST
@login_required
@user_passes_test(is_admin_or_manager)
def test_user_permissions(request):
    """Test what a specific user can see based on their profile"""
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        module_name = data.get('module')
        model_name = data.get('model')
        
        from django.contrib.auth.models import User
        user = get_object_or_404(User, id=user_id)
        
        if not hasattr(user, 'user_profile') or not user.user_profile.profile:
            return JsonResponse({
                'success': False,
                'message': 'User has no profile assigned'
            })
        
        profile = user.user_profile.profile
        
        # Get visible fields
        visible_fields = profile.get_visible_fields(module_name, model_name)
        
        # Get field permissions
        permissions = FieldPermission.objects.filter(
            profile=profile,
            module__name=module_name,
            model_name=model_name,
            is_active=True
        ).values('field_name', 'can_view', 'can_edit', 'is_visible_in_list', 'is_visible_in_detail', 'is_visible_in_forms')
        
        # Get data filters
        data_filters = DataFilter.objects.filter(
            profile=profile,
            module__name=module_name,
            model_name=model_name,
            is_active=True
        ).values('name', 'filter_type', 'filter_conditions')
        
        return JsonResponse({
            'success': True,
            'user': user.get_full_name() or user.username,
            'profile': profile.name,
            'visible_fields': visible_fields,
            'field_permissions': list(permissions),
            'data_filters': list(data_filters),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)