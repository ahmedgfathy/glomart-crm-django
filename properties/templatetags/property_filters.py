from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency_format(value, currency_symbol=None):
    """Format a number with proper thousands separators and currency symbol"""
    if value is None:
        return "N/A"
    
    # Default currency symbol if none provided
    if not currency_symbol:
        currency_symbol = "AED"
    
    try:
        # Convert to float if it's a string or Decimal
        if isinstance(value, (str, Decimal)):
            value = float(value)
        
        # Format with thousands separators
        formatted = f"{value:,.0f}"
        return f"{currency_symbol} {formatted}"
    except (ValueError, TypeError):
        return "N/A"

@register.filter
def number_format(value):
    """Format a number with proper thousands separators"""
    if value is None:
        return "N/A"
    
    try:
        # Convert to float if it's a string or Decimal
        if isinstance(value, (str, Decimal)):
            value = float(value)
        
        # Format with thousands separators
        return f"{value:,.0f}"
    except (ValueError, TypeError):
        return "N/A"

@register.filter
def split(value, delimiter=","):
    """Split a string by delimiter"""
    if value is None:
        return []
    
    try:
        return str(value).split(delimiter)
    except (ValueError, TypeError):
        return []

@register.filter
def strip(value):
    """Strip whitespace from a string"""
    if value is None:
        return ""
    
    try:
        return str(value).strip()
    except (ValueError, TypeError):
        return str(value)

@register.filter
def div(value, divisor):
    """Divide two numbers"""
    if value is None or divisor is None:
        return 0
    
    try:
        dividend = float(value)
        divisor_val = float(divisor)
        
        if divisor_val == 0:
            return 0
        
        return dividend / divisor_val
    except (ValueError, TypeError, ZeroDivisionError):
        return 0