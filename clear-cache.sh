#!/bin/bash
# Clear all caches and restart services

echo "🧹 Clearing Django cache..."
cd /var/www/glomart-crm
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

echo "📦 Collecting static files..."
source venv/bin/activate
DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production python manage.py collectstatic --noinput --clear | tail -2

echo "🔄 Restarting services..."
sudo systemctl restart glomart-crm
sudo systemctl restart nginx

echo "✅ Cache cleared and services restarted!"
echo "👉 Now do a HARD REFRESH in your browser:"
echo "   - Windows/Linux: Ctrl+Shift+R or Ctrl+F5"
echo "   - Mac: Cmd+Shift+R"
echo "   - Or open Incognito/Private window"
