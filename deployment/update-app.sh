#!/bin/bash
# Glomart CRM - Quick Update Script
# Run this script as django-user to update the application

set -e

APP_DIR="/var/www/glomart-crm"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

cd $APP_DIR

print_status "🔄 Updating Glomart CRM..."

# Backup current version
print_status "Creating backup..."
sudo /usr/local/bin/backup-crm.sh

# Pull latest changes
print_status "Pulling latest code..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
print_status "Updating dependencies..."
pip install -r requirements.txt

# Run migrations
print_status "Running migrations..."
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
python manage.py migrate

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Clear cache (if Redis is configured)
print_status "Clearing cache..."
python manage.py shell -c "from django.core.cache import cache; cache.clear()" 2>/dev/null || echo "Cache not configured"

# Restart services
print_status "Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl reload nginx

# Check status
if systemctl is-active --quiet gunicorn; then
    print_status "✅ Update completed successfully!"
    print_status "Gunicorn is running"
else
    print_warning "⚠️ Gunicorn failed to start. Check logs:"
    echo "sudo journalctl -u gunicorn -n 50"
fi

if systemctl is-active --quiet nginx; then
    print_status "Nginx is running"
else
    print_warning "⚠️ Nginx failed to start. Check logs:"
    echo "sudo tail -f /var/log/nginx/error.log"
fi

print_status "Application URL: https://$(grep ALLOWED_HOSTS .env | cut -d'=' -f2 | cut -d',' -f1)"