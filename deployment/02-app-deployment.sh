#!/bin/bash
# Glomart CRM - Application Deployment Script
# Run this script as django-user after server setup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_input() {
    echo -e "${BLUE}[INPUT]${NC} $1"
}

# Check if running as django-user
if [ "$USER" != "django-user" ]; then
    print_error "Please run this script as django-user"
    exit 1
fi

APP_DIR="/var/www/glomart-crm"

print_status "🚀 Starting Glomart CRM Application Deployment..."

# Get user inputs
print_input "Enter your GitHub repository URL:"
read -r REPO_URL

print_input "Enter your domain name (e.g., yoursite.com):"
read -r DOMAIN_NAME

print_input "Enter your server IP address:"
read -r SERVER_IP

print_input "Enter database name [glomart_crm]:"
read -r DB_NAME
DB_NAME=${DB_NAME:-glomart_crm}

print_input "Enter database username [crm_user]:"
read -r DB_USER
DB_USER=${DB_USER:-crm_user}

print_input "Enter database password:"
read -s DB_PASSWORD
echo

print_input "Enter Django secret key (leave empty to generate):"
read -r SECRET_KEY
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
fi

print_status "Cloning repository..."
cd $APP_DIR
if [ ! -d ".git" ]; then
    git clone $REPO_URL .
else
    git pull origin main
fi

print_status "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn python-decouple pymysql

print_status "Creating environment configuration..."
cat > .env << EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN_NAME,www.$DOMAIN_NAME,$SERVER_IP

# Database Configuration
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=3306

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY

# Static and Media Files
STATIC_ROOT=/var/www/glomart-crm/staticfiles
MEDIA_ROOT=/var/www/glomart-crm/media

# Email Configuration (Update with your SMTP settings)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EOF

print_status "Creating production settings..."
cat > real_estate_crm/settings_production.py << 'EOF'
import os
from decouple import config

# Import base settings
from .settings import *

# Production overrides
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = config('STATIC_ROOT')
MEDIA_URL = '/media/'
MEDIA_ROOT = config('MEDIA_ROOT')

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='DENY')

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Logging
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
            'filename': '/var/www/glomart-crm/logs/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'glomart_crm': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
EOF

print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p media
mkdir -p staticfiles

print_status "Setting up database..."
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production

print_warning "Make sure the database and user are created in MariaDB:"
echo "CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
echo "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
echo "FLUSH PRIVILEGES;"
echo

print_input "Press Enter after creating the database and user..."
read

print_status "Running migrations..."
python manage.py migrate

print_status "Creating superuser..."
python manage.py createsuperuser

print_status "Collecting static files..."
python manage.py collectstatic --noinput

print_status "Creating residential users..."
if [ -f "authentication/management/commands/create_residential_users_v2.py" ]; then
    python manage.py create_residential_users_v2
else
    print_warning "Residential users command not found. You can create them later."
fi

print_status "✅ Application deployment completed!"
echo
print_warning "Next steps:"
echo "1. Configure Gunicorn service (run sudo ./03-configure-services.sh)"
echo "2. Configure Nginx (update domain name)"
echo "3. Set up SSL certificate with certbot"
echo "4. Test the application"