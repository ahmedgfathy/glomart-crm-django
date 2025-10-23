from django.utils import timezone
from .models import UserActivity, Module


def log_user_activity(user, activity_type, module_name=None, description='', request=None):
    """
    Log user activity for audit purposes
    
    Args:
        user: Django User object
        activity_type (str): Type of activity ('login', 'logout', 'view', 'create', 'edit', 'delete', 'export', 'import')
        module_name (str, optional): Name of the module
        description (str, optional): Additional description
        request (HttpRequest, optional): Django request object for IP/user agent
    """
    try:
        # Get module object if module_name is provided
        module = None
        if module_name:
            try:
                module = Module.objects.get(name=module_name)
            except Module.DoesNotExist:
                # If module doesn't exist, still log but without module reference
                pass
        
        # Extract IP address and user agent from request if provided
        ip_address = None
        user_agent = ''
        
        if request:
            # Get IP address from various headers (for proxies, load balancers)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]  # Limit length
        
        # Create activity record
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            module=module,
            description=description[:500],  # Limit description length
            ip_address=ip_address,
            user_agent=user_agent
        )
        
    except Exception as e:
        # Don't let logging errors break the main functionality
        # In production, you might want to log this error to a separate logging system
        print(f"Error logging user activity: {e}")


def get_client_ip(request):
    """
    Extract client IP address from request, handling proxies and load balancers
    
    Args:
        request: Django HttpRequest object
    
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def format_activity_description(action, model_name, object_name=None):
    """
    Format a standardized activity description
    
    Args:
        action (str): The action performed (e.g., 'created', 'updated', 'deleted')
        model_name (str): Name of the model/object type
        object_name (str, optional): Name or identifier of the specific object
    
    Returns:
        str: Formatted description
    """
    if object_name:
        return f"{action.title()} {model_name} '{object_name}'"
    else:
        return f"{action.title()} {model_name}"


def check_rate_limit(user, activity_type, time_window_minutes=5, max_attempts=10):
    """
    Check if user has exceeded rate limit for a specific activity type
    
    Args:
        user: Django User object
        activity_type (str): Type of activity to check
        time_window_minutes (int): Time window in minutes to check
        max_attempts (int): Maximum attempts allowed in time window
    
    Returns:
        bool: True if user is within rate limit, False if exceeded
    """
    try:
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        recent_activities = UserActivity.objects.filter(
            user=user,
            activity_type=activity_type,
            timestamp__gte=cutoff_time
        ).count()
        
        return recent_activities < max_attempts
        
    except Exception as e:
        # If rate limiting fails, allow the action (fail open)
        print(f"Error checking rate limit: {e}")
        return True


def get_user_activity_stats(user, days=30):
    """
    Get user activity statistics for the past N days
    
    Args:
        user: Django User object
        days (int): Number of days to look back
    
    Returns:
        dict: Dictionary with activity statistics
    """
    try:
        from datetime import timedelta
        from django.db.models import Count
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        activities = UserActivity.objects.filter(
            user=user,
            timestamp__gte=cutoff_date
        )
        
        # Count by activity type
        activity_counts = activities.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Count by module
        module_counts = activities.filter(
            module__isnull=False
        ).values('module__name', 'module__display_name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        total_activities = activities.count()
        
        return {
            'total_activities': total_activities,
            'activity_types': list(activity_counts),
            'module_usage': list(module_counts),
            'days_covered': days
        }
        
    except Exception as e:
        print(f"Error getting user activity stats: {e}")
        return {
            'total_activities': 0,
            'activity_types': [],
            'module_usage': [],
            'days_covered': days
        }