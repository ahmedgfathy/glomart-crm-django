from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Look up a key in a dictionary"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0

@register.filter  
def get_permission_level(permissions_dict, module_name):
    """Get permission level for a specific module"""
    if isinstance(permissions_dict, dict):
        return permissions_dict.get(module_name, 0)
    return 0