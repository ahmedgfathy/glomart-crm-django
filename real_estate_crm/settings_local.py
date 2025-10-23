"""
Local Django settings for Glomart CRM
This file overrides settings.py for local development
"""

from .settings import *
from decouple import config
import os

# Load .env.local file
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env.local'))

# Override database settings for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='django_db_glomart_rs'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default='zerocall'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Local development settings
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda x: [s.strip() for s in x.split(',')])

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