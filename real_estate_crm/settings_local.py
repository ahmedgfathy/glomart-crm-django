"""
Local Django settings for Glomart CRM
This file overrides settings.py for local development
"""

from .settings import *

# Override database settings for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'glomart_crm_local',
        'USER': 'glomart_local',
        'PASSWORD': 'local123',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Local development settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Disable HTTPS redirect for local development
SECURE_SSL_REDIRECT = False

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files configuration for local development
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "public",
]

# Media files configuration for local development  
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

print("🏠 Using LOCAL development settings")
print(f"🗄️ Database: {DATABASES['default']['NAME']}")
print(f"👤 User: {DATABASES['default']['USER']}")