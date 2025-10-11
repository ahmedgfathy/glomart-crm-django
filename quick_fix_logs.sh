#!/bin/bash
# Quick fix for the log directory issue
# Run this on the production server immediately

echo "🔧 QUICK FIX: Creating missing log directory"
echo "============================================"

# Create the log directory
mkdir -p /var/log/glomart-crm
chown www-data:www-data /var/log/glomart-crm
chmod 755 /var/log/glomart-crm

echo "✅ Log directory created: /var/log/glomart-crm"

# Test Django settings now
cd /var/www/glomart-crm
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production

echo "🧪 Testing Django settings..."
python manage.py check --deploy

if [ $? -eq 0 ]; then
    echo "✅ Django settings working!"
    
    # Collect static files
    echo "📄 Collecting static files..."
    python manage.py collectstatic --noinput
    
    # Restart services
    echo "🔄 Restarting services..."
    systemctl daemon-reload
    systemctl restart glomart-crm
    
    echo "🎉 FIXED! Your site should work now."
    echo "🌐 Check: https://sys.glomartrealestates.com"
else
    echo "❌ Still have issues, check the output above"
fi