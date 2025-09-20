from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup dictionary values"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None

@register.filter
def field_permission_lookup(field_permissions, profile_id):
    """Look up field permissions for a specific profile"""
    if isinstance(field_permissions, dict):
        return field_permissions.get(str(profile_id), {})
    return {}

@register.filter
def multiply(value, arg):
    """Multiply two values"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.filter
def split(value, arg):
    """Split string by delimiter"""
    return value.split(arg)

@register.filter
def join_with(value, arg):
    """Join list with delimiter"""
    if isinstance(value, list):
        return arg.join(value)
    return value