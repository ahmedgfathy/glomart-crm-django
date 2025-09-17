from .signals import set_current_request, clear_current_request


class AuditMiddleware:
    """
    Middleware to track current request for audit logging
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set the current request in thread-local storage
        set_current_request(request)
        
        try:
            response = self.get_response(request)
        finally:
            # Clear the request after processing
            clear_current_request()
        
        return response