from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Template filter to look up a value in a dictionary or object by key.
    Usage: {{ dict|lookup:key }}
    """
    if hasattr(dictionary, key):
        return getattr(dictionary, key)
    elif hasattr(dictionary, '__getitem__'):
        try:
            return dictionary[key]
        except (KeyError, TypeError):
            return None
    return None

@register.filter
def get_item(dictionary, key):
    """
    Alternative filter for dictionary lookup
    """
    try:
        return dictionary.get(key) if hasattr(dictionary, 'get') else dictionary[key]
    except (KeyError, TypeError, AttributeError):
        return None

@register.simple_tag
def multiply(value, multiplier):
    """
    Multiply two values
    """
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """
    Calculate percentage
    """
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0