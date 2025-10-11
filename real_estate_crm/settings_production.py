"""
Production Django settings for real_estate_crm project.
This file is used ONLY for production deployment.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env.production file (if exists)
env_file = BASE_DIR / '.env.production'
if env_file.exists():
    load_dotenv(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-CHANGE-THIS-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Get allowed hosts from environment variable
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'sys.glomartrealestates.com,5.180.148.92').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication',
    'leads',
    'properties',  # Property management app
    'projects',    # Project management app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'leads.middleware.UserActivityMiddleware',  # Custom middleware for activity tracking
]

ROOT_URLCONF = 'real_estate_crm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'authentication.enhanced_context_processors.enhanced_module_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'real_estate_crm.wsgi.application'

# Database - Production MariaDB (using environment variables)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'django_db_glomart_rs'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'ZeroCall20!@HH##1655&&'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 60,  # Connection pooling for production
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/var/www/glomart-crm/staticfiles')

STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "public",  # Match main settings
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/var/www/glomart-crm/media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
#AUTH_USER_MODEL = .authentication.User. # Removed - using default User model

# Login URLs
LOGIN_URL = '/authentication/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/authentication/login/'

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session security
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
CSRF_COOKIE_SECURE = False     # Set to True if using HTTPS
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/glomart-crm/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}