# Production Media File Settings for Django
# Add these to your Django settings when deployed

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/glomart-crm/media'

# Static files configuration  
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/glomart-crm/staticfiles'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

# Security settings for file uploads
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv']
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

# Property image handling
PROPERTY_IMAGE_UPLOAD_PATH = 'property-images/'
PROPERTY_VIDEO_UPLOAD_PATH = 'property-videos/'
PROPERTY_DOCUMENT_UPLOAD_PATH = 'documents/'

# URL patterns for property media
PROPERTY_IMAGE_URL_PATTERN = '/media/property-images/'
PROPERTY_VIDEO_URL_PATTERN = '/media/property-videos/'