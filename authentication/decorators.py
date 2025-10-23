from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import UserProfile, Module, Permission


def permission_required(module_name, permission_code):
    """
    Decorator to check if user has specific permission for a module
    
    Args:
        module_name (str): Name of the module (e.g., 'leads', 'properties', 'projects')
        permission_code (str): Permission code (e.g., 'view', 'create', 'edit', 'delete')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Superuser has all permissions
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            try:
                user_profile = request.user.user_profile
                if not user_profile or not user_profile.profile:
                    messages.error(request, 'Access denied. No profile assigned.')
                    return redirect('authentication:dashboard')
                
                # Check if user has the required permission
                has_permission = user_profile.has_permission(module_name, permission_code)
                
                if not has_permission:
                    messages.error(request, f'Access denied. You do not have permission to {permission_code} {module_name}.')
                    return redirect('authentication:dashboard')
                
                return view_func(request, *args, **kwargs)
                
            except UserProfile.DoesNotExist:
                messages.error(request, 'Access denied. No profile assigned.')
                return redirect('authentication:dashboard')
            except Exception as e:
                messages.error(request, 'Access denied. Permission check failed.')
                return redirect('authentication:dashboard')
        
        return _wrapped_view
    return decorator


def permission_required_ajax(module_name, permission_code):
    """
    Decorator to check permissions for AJAX requests
    Returns JSON response instead of redirect
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Superuser has all permissions
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            try:
                user_profile = request.user.user_profile
                if not user_profile or not user_profile.profile:
                    return JsonResponse({'error': 'Access denied. No profile assigned.'}, status=403)
                
                # Check if user has the required permission
                has_permission = user_profile.has_permission(module_name, permission_code)
                
                if not has_permission:
                    return JsonResponse({
                        'error': f'Access denied. You do not have permission to {permission_code} {module_name}.'
                    }, status=403)
                
                return view_func(request, *args, **kwargs)
                
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'Access denied. No profile assigned.'}, status=403)
            except Exception as e:
                return JsonResponse({'error': 'Access denied. Permission check failed.'}, status=403)
        
        return _wrapped_view
    return decorator


def module_access_required(module_name):
    """
    Decorator to check if user has access to a module (any permission level)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Superuser has all access
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            try:
                user_profile = request.user.user_profile
                if not user_profile or not user_profile.profile:
                    messages.error(request, 'Access denied. No profile assigned.')
                    return redirect('authentication:dashboard')
                
                # Check if user has any permission for this module
                accessible_modules = user_profile.get_accessible_modules()
                has_access = accessible_modules.filter(name=module_name).exists()
                
                if not has_access:
                    messages.error(request, f'Access denied. You do not have access to {module_name} module.')
                    return redirect('authentication:dashboard')
                
                return view_func(request, *args, **kwargs)
                
            except UserProfile.DoesNotExist:
                messages.error(request, 'Access denied. No profile assigned.')
                return redirect('authentication:dashboard')
            except Exception as e:
                messages.error(request, 'Access denied. Module access check failed.')
                return redirect('authentication:dashboard')
        
        return _wrapped_view
    return decorator


def superuser_required(view_func):
    """
    Decorator to require superuser access
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Access denied. Administrator privileges required.')
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def check_permission_level(user, module_name, required_level):
    """
    Helper function to check if user has minimum permission level for a module
    
    Args:
        user: Django User object
        module_name (str): Name of the module
        required_level (int): Required permission level (1=View, 2=Edit, 3=Create, 4=Delete)
    
    Returns:
        bool: True if user has required permission level or higher
    """
    if user.is_superuser:
        return True
    
    try:
        user_profile = user.user_profile
        if not user_profile or not user_profile.profile:
            return False
        
        max_level = user_profile.get_max_permission_level(module_name)
        return max_level >= required_level
        
    except (UserProfile.DoesNotExist, AttributeError):
        return False


def has_permission(user, module_name, permission_code):
    """
    Helper function to check if user has specific permission
    
    Args:
        user: Django User object
        module_name (str): Name of the module
        permission_code (str): Permission code
    
    Returns:
        bool: True if user has the permission
    """
    if user.is_superuser:
        return True
    
    try:
        user_profile = user.user_profile
        if not user_profile or not user_profile.profile:
            return False
        
        return user_profile.has_permission(module_name, permission_code)
        
    except (UserProfile.DoesNotExist, AttributeError):
        return False