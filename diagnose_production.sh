#!/bin/bash
# Quick Production Status Check
# Run this script ON the production server to diagnose issues

echo "🔍 PRODUCTION STATUS DIAGNOSIS"
echo "=============================="

# Check current directory
echo "📁 Current directory: $(pwd)"
if [[ ! -d "/var/www/glomart-crm" ]]; then
    echo "❌ Not on production server - /var/www/glomart-crm not found"
    exit 1
fi

cd /var/www/glomart-crm

echo ""
echo "🐍 Python Environment:"
echo "Python: $(python3 --version)"
echo "Virtual env: $(ls -la venv/ | head -2)"

echo ""
echo "⚙️ Django Settings:"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-Not set}"

# Check current settings
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    echo "Current Django settings in use:"
    python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()
from django.conf import settings
print(f'Settings module: {settings.SETTINGS_MODULE}')
print(f'Debug mode: {settings.DEBUG}')
print(f'Database name: {settings.DATABASES[\"default\"][\"NAME\"]}')
print(f'Database user: {settings.DATABASES[\"default\"][\"USER\"]}')
" 2>/dev/null || echo "❌ Django settings check failed"
fi

echo ""
echo "🗄️ Database Status:"
if mysql -h localhost -u root -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database connection: OK"
    echo "Tables:"
    mysql -h localhost -u root -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SHOW TABLES;" 2>/dev/null | head -10
else
    echo "❌ Database connection: FAILED"
fi

echo ""
echo "🔧 Service Status:"
echo "Glomart CRM service: $(systemctl is-active glomart-crm 2>/dev/null || echo 'not found')"
echo "Nginx service: $(systemctl is-active nginx 2>/dev/null || echo 'not found')"

echo ""
echo "📄 Configuration Files:"
echo "Service file: $(ls -la /etc/systemd/system/glomart-crm.service 2>/dev/null || echo 'Not found')"
echo "Environment file: $(ls -la .env.production 2>/dev/null || echo 'Not found')"
echo "Gunicorn config: $(ls -la gunicorn.conf.py 2>/dev/null || echo 'Not found')"

echo ""
echo "🌐 Application Test:"
if curl -f -s http://127.0.0.1:8000/admin/ >/dev/null 2>&1; then
    echo "✅ Application responding: OK"
else
    echo "❌ Application responding: FAILED"
    echo ""
    echo "📋 Recent service logs:"
    journalctl -u glomart-crm -n 10 --no-pager 2>/dev/null || echo "No service logs available"
fi

echo ""
echo "💡 RECOMMENDED ACTION:"
echo "If you see issues above, run: ./fix_production_settings.sh"