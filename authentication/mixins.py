from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from authentication.models import Module, Profile

class EnhancedRBACMixin(LoginRequiredMixin):
    """Mixin to handle enhanced RBAC permissions"""
    
    required_module = None
    required_permission_level = 1  # 1=view, 2=edit, 3=create, 4=delete
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Check if user has required permissions
        if not self.has_permission(request):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_permission(self, request):
        """Check if user has required permission"""
        if not self.required_module:
            return True
        
        try:
            user_profile = request.user.user_profile
            if not user_profile or not user_profile.profile:
                return False
            
            module = Module.objects.filter(name=self.required_module).first()
            if not module:
                return False
            
            permissions = user_profile.profile.permissions.filter(
                module=module,
                level__gte=self.required_permission_level,
                is_active=True
            )
            
            return permissions.exists()
        except:
            return False
    
    def get_user_profile(self):
        """Get current user's profile"""
        try:
            return self.request.user.user_profile.profile
        except:
            return None
    
    def apply_data_scope_to_queryset(self, queryset, model_name):
        """Apply data scope filters to queryset"""
        profile = self.get_user_profile()
        if profile and self.required_module:
            return profile.apply_data_scope(queryset, self.required_module, self.request.user)
        return queryset
    
    def apply_data_filters_to_queryset(self, queryset, model_name):
        """Apply data filters to queryset"""
        profile = self.get_user_profile()
        if profile and self.required_module:
            return profile.apply_data_filters(queryset, self.required_module, model_name)
        return queryset
    
    def get_visible_fields(self, model_name, context_type='list'):
        """Get visible fields for current user"""
        profile = self.get_user_profile()
        if profile and self.required_module:
            return profile.get_visible_fields(self.required_module, model_name, context_type)
        return None

class LeadsRBACMixin(EnhancedRBACMixin):
    """RBAC mixin for leads module"""
    required_module = 'leads'

class PropertiesRBACMixin(EnhancedRBACMixin):
    """RBAC mixin for properties module"""
    required_module = 'property'

class ProjectsRBACMixin(EnhancedRBACMixin):
    """RBAC mixin for projects module"""
    required_module = 'projects'

class ViewPermissionMixin(EnhancedRBACMixin):
    """Mixin for view permissions (level 1)"""
    required_permission_level = 1

class EditPermissionMixin(EnhancedRBACMixin):
    """Mixin for edit permissions (level 2)"""
    required_permission_level = 2

class CreatePermissionMixin(EnhancedRBACMixin):
    """Mixin for create permissions (level 3)"""
    required_permission_level = 3

class DeletePermissionMixin(EnhancedRBACMixin):
    """Mixin for delete permissions (level 4)"""
    required_permission_level = 4

# Combined mixins for common use cases
class LeadsViewMixin(LeadsRBACMixin, ViewPermissionMixin):
    """View permission for leads"""
    pass

class LeadsEditMixin(LeadsRBACMixin, EditPermissionMixin):
    """Edit permission for leads"""
    pass

class LeadsCreateMixin(LeadsRBACMixin, CreatePermissionMixin):
    """Create permission for leads"""
    pass

class LeadsDeleteMixin(LeadsRBACMixin, DeletePermissionMixin):
    """Delete permission for leads"""
    pass

class PropertiesViewMixin(PropertiesRBACMixin, ViewPermissionMixin):
    """View permission for properties"""
    pass

class PropertiesEditMixin(PropertiesRBACMixin, EditPermissionMixin):
    """Edit permission for properties"""
    pass

class PropertiesCreateMixin(PropertiesRBACMixin, CreatePermissionMixin):
    """Create permission for properties"""
    pass

class PropertiesDeleteMixin(PropertiesRBACMixin, DeletePermissionMixin):
    """Delete permission for properties"""
    pass

class ProjectsViewMixin(ProjectsRBACMixin, ViewPermissionMixin):
    """View permission for projects"""
    pass

class ProjectsEditMixin(ProjectsRBACMixin, EditPermissionMixin):
    """Edit permission for projects"""
    pass

class ProjectsCreateMixin(ProjectsRBACMixin, CreatePermissionMixin):
    """Create permission for projects"""
    pass

class ProjectsDeleteMixin(ProjectsRBACMixin, DeletePermissionMixin):
    """Delete permission for projects"""
    pass