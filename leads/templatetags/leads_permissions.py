from django import template
from authentication.models import Module

register = template.Library()

@register.filter
def has_leads_view_permission(user):
    """Check if user has view permission for leads module"""
    if user.is_superuser:
        return True
    
    try:
        user_profile = user.user_profile
        leads_module = Module.objects.get(name='leads')
        
        # Check for view permission (level 1)
        permissions = user_profile.profile.permissions.filter(
            module=leads_module,
            level__gte=1,
            is_active=True
        )
        return permissions.exists()
    except:
        return False

@register.filter
def has_leads_create_permission(user):
    """Check if user has create permission for leads module"""
    if user.is_superuser:
        return True
    
    try:
        user_profile = user.user_profile
        leads_module = Module.objects.get(name='leads')
        
        # Check for create permission (level 3)
        permissions = user_profile.profile.permissions.filter(
            module=leads_module,
            level__gte=3,
            is_active=True
        )
        return permissions.exists()
    except:
        return False

@register.filter
def has_leads_edit_permission(user):
    """Check if user has edit permission for leads module"""
    if user.is_superuser:
        return True
    
    try:
        user_profile = user.user_profile
        leads_module = Module.objects.get(name='leads')
        
        # Check for edit permission (level 2)
        permissions = user_profile.profile.permissions.filter(
            module=leads_module,
            level__gte=2,
            is_active=True
        )
        return permissions.exists()
    except:
        return False

@register.filter
def has_leads_delete_permission(user):
    """Check if user has delete permission for leads module"""
    if user.is_superuser:
        return True
    
    try:
        user_profile = user.user_profile
        leads_module = Module.objects.get(name='leads')
        
        # Check for delete permission (level 4)
        permissions = user_profile.profile.permissions.filter(
            module=leads_module,
            level__gte=4,
            is_active=True
        )
        return permissions.exists()
    except:
        return False