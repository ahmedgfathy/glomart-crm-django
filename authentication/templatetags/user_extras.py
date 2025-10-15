from django import template

register = template.Library()

@register.filter
def get_initials(user):
    """Get user initials from full name or username."""
    full_name = user.get_full_name()
    if full_name:
        parts = full_name.strip().split()
        if len(parts) >= 2:
            # First letter of first name + first letter of last name
            return (parts[0][0] + parts[-1][0]).upper()
        else:
            # Just first two letters of single name
            return full_name[:2].upper() if len(full_name) >= 2 else full_name.upper()
    else:
        # Use username
        username = user.username
        return username[:2].upper() if len(username) >= 2 else username.upper()
