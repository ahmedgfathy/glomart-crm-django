from django import template
from django.utils.safestring import mark_safe
from authentication.models import Profile

register = template.Library()

@register.filter
def field_visible(field_name, visible_fields):
    """Check if a field is visible to the current user"""
    if not visible_fields:
        return True  # If no restrictions, show all fields
    return field_name in visible_fields

@register.filter
def get_field_value(obj, field_name):
    """Get the value of a field from an object"""
    try:
        return getattr(obj, field_name, '')
    except:
        return ''

@register.filter
def get_verbose_field_name(model_class, field_name):
    """Get the verbose name of a model field"""
    try:
        field = model_class._meta.get_field(field_name)
        return field.verbose_name
    except:
        return field_name.replace('_', ' ').title()

@register.simple_tag
def render_field_if_visible(obj, field_name, visible_fields, css_class=""):
    """Render a field value only if it's visible to the user"""
    if not visible_fields or field_name in visible_fields:
        value = get_field_value(obj, field_name)
        if value:
            return mark_safe(f'<span class="{css_class}">{value}</span>')
    return ""

@register.simple_tag
def render_form_field_if_visible(form_field, field_name, visible_fields, css_class=""):
    """Render a form field only if it's visible to the user"""
    if not visible_fields or field_name in visible_fields:
        if hasattr(form_field, 'as_widget'):
            widget_html = form_field.as_widget(attrs={'class': css_class})
            return mark_safe(widget_html)
        else:
            return mark_safe(f'<span class="{css_class}">{form_field}</span>')
    return ""

@register.inclusion_tag('authentication/field_permission_widget.html')
def field_permission_widget(field_name, visible_fields, form_fields=None):
    """Widget to show/hide fields based on permissions"""
    return {
        'field_name': field_name,
        'is_visible': not visible_fields or field_name in visible_fields,
        'is_form_field': form_fields and field_name in form_fields,
    }

@register.filter
def apply_data_filters(queryset, profile):
    """Apply data filters to a queryset based on user profile"""
    if not profile:
        return queryset
    
    # This would be called from views, not templates typically
    # But provided for template convenience
    return queryset

@register.simple_tag(takes_context=True)
def user_can_see_field(context, module_name, model_name, field_name, context_type='list'):
    """Check if current user can see a specific field"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    if request.user.is_superuser:
        return True
    
    try:
        user_profile = request.user.user_profile
        if user_profile and user_profile.profile:
            visible_fields = user_profile.profile.get_visible_fields(module_name, model_name, context_type)
            return not visible_fields or field_name in visible_fields
    except:
        pass
    
    return False

@register.simple_tag(takes_context=True)
def get_filtered_choices(context, module_name, model_name, field_name):
    """Get filtered choices for a dropdown field based on user profile"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return []
    
    if request.user.is_superuser:
        # Return all choices for superuser
        return []
    
    try:
        user_profile = request.user.user_profile
        if user_profile and user_profile.profile:
            from authentication.models import Module, DynamicDropdown
            
            module = Module.objects.filter(name=module_name).first()
            if module:
                dropdown = DynamicDropdown.objects.filter(
                    profile=user_profile.profile,
                    module=module,
                    model_name=model_name,
                    field_name=field_name,
                    is_active=True
                ).first()
                
                if dropdown:
                    # Return filtered choices
                    return dropdown.allowed_values.split(',') if dropdown.allowed_values else []
    except:
        pass
    
    return []

@register.simple_tag
def render_property_type_badge(property_type):
    """Render a colored badge for property type"""
    type_colors = {
        'commercial': 'bg-primary',
        'residential': 'bg-success',
        'industrial': 'bg-warning',
        'land': 'bg-info',
        'mixed_use': 'bg-secondary',
    }
    
    color_class = type_colors.get(property_type.lower(), 'bg-dark')
    display_name = property_type.replace('_', ' ').title()
    
    return mark_safe(f'<span class="badge {color_class}">{display_name}</span>')

@register.simple_tag
def render_lead_status_badge(status):
    """Render a colored badge for lead status"""
    status_colors = {
        'new': 'bg-info',
        'contacted': 'bg-warning',
        'qualified': 'bg-primary',
        'proposal': 'bg-secondary',
        'negotiation': 'bg-warning text-dark',
        'closed_won': 'bg-success',
        'closed_lost': 'bg-danger',
        'follow_up': 'bg-info',
    }
    
    color_class = status_colors.get(status.lower(), 'bg-dark')
    display_name = status.replace('_', ' ').title()
    
    return mark_safe(f'<span class="badge {color_class}">{display_name}</span>')

@register.simple_tag
def render_project_status_badge(status):
    """Render a colored badge for project status"""
    status_colors = {
        'planning': 'bg-info',
        'in_progress': 'bg-warning',
        'completed': 'bg-success',
        'on_hold': 'bg-secondary',
        'cancelled': 'bg-danger',
    }
    
    color_class = status_colors.get(status.lower(), 'bg-dark')
    display_name = status.replace('_', ' ').title()
    
    return mark_safe(f'<span class="badge {color_class}">{display_name}</span>')