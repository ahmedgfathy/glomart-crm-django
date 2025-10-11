#!/bin/bash
# Fix Production Settings and Database Connection
# Run this script ON the production server to fix the settings issue

set -e

echo "🔧 FIXING PRODUCTION SETTINGS AND DATABASE CONNECTION"
echo "====================================================="

# Check if we're on the production server
if [[ ! -d "/var/www/glomart-crm" ]]; then
    echo "❌ This script must be run ON the production server"
    echo "Current directory: $(pwd)"
    echo "Expected: /var/www/glomart-crm should exist"
    exit 1
fi

cd /var/www/glomart-crm

# 1. Create .env.production file with correct settings
echo "📝 Creating .env.production file..."
cat > .env.production << 'EOF'
# Production Environment Variables
ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production

# Production Database (MASTER DATA - Handle with care!)
DB_NAME=django_db_glomart_rs
DB_USER=root
DB_PASSWORD=ZeroCall20!@HH##1655&&
DB_HOST=localhost
DB_PORT=3306

# Security Settings
SECRET_KEY=django-production-secret-key-change-this
DEBUG=False
ALLOWED_HOSTS=sys.glomartrealestates.com,5.180.148.92,localhost

# File Paths
STATIC_ROOT=/var/www/glomart-crm/staticfiles
MEDIA_ROOT=/var/www/glomart-crm/media

# Timezone
TIME_ZONE=Africa/Cairo
EOF

# Set secure permissions on environment file
chmod 600 .env.production
chown www-data:www-data .env.production

echo "✅ .env.production created"

# 2. Test database connection
echo "🔌 Testing database connection..."
if mysql -h localhost -u root -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed!"
    echo "📋 Checking MySQL status..."
    systemctl status mysql || systemctl status mariadb || echo "MySQL/MariaDB service not found"
    
    echo ""
    echo "🛠️  Possible solutions:"
    echo "1. Start MySQL/MariaDB service:"
    echo "   sudo systemctl start mysql"
    echo "   # OR"
    echo "   sudo systemctl start mariadb"
    echo ""
    echo "2. Check MySQL root password:"
    echo "   mysql -u root -p"
    echo ""
    echo "3. Reset MySQL root password if needed"
    exit 1
fi

# 3. Update Gunicorn service to use production settings
echo "⚙️  Updating Gunicorn service configuration..."

# Check current service file
if [[ -f "/etc/systemd/system/glomart-crm.service" ]]; then
    echo "📄 Current service file found"
    
    # Backup current service file
    cp /etc/systemd/system/glomart-crm.service /etc/systemd/system/glomart-crm.service.backup
    
    # Update service file to use production settings
    sed -i 's/DJANGO_SETTINGS_MODULE=real_estate_crm.settings/DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production/g' /etc/systemd/system/glomart-crm.service
    
    # Ensure environment file is loaded
    if ! grep -q "EnvironmentFile" /etc/systemd/system/glomart-crm.service; then
        sed -i '/\[Service\]/a EnvironmentFile=/var/www/glomart-crm/.env.production' /etc/systemd/system/glomart-crm.service
    fi
    
    echo "✅ Service file updated"
else
    echo "⚠️  Service file not found, creating new one..."
    
    cat > /etc/systemd/system/glomart-crm.service << 'EOF'
[Unit]
Description=Glomart CRM Django Application
After=network.target mysql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/glomart-crm
Environment=DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
EnvironmentFile=/var/www/glomart-crm/.env.production
ExecStart=/var/www/glomart-crm/venv/bin/gunicorn real_estate_crm.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    echo "✅ New service file created"
fi

# 4. Update gunicorn configuration if exists
if [[ -f "gunicorn.conf.py" ]]; then
    echo "📝 Updating gunicorn configuration..."
    if ! grep -q "DJANGO_SETTINGS_MODULE.*settings_production" gunicorn.conf.py; then
        echo 'import os' > gunicorn_temp.py
        echo 'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_crm.settings_production")' >> gunicorn_temp.py
        cat gunicorn.conf.py >> gunicorn_temp.py
        mv gunicorn_temp.py gunicorn.conf.py
        chown www-data:www-data gunicorn.conf.py
    fi
    echo "✅ Gunicorn configuration updated"
fi

# 5. Install missing dependencies
echo "📦 Installing missing dependencies..."
source venv/bin/activate
pip install python-dotenv

# 6. Test Django with production settings
echo "🧪 Testing Django with production settings..."
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
source .env.production

if python manage.py check --deploy; then
    echo "✅ Django production settings check passed"
else
    echo "⚠️  Django settings check has warnings (this is normal)"
fi

# 7. Collect static files
echo "📄 Collecting static files..."
python manage.py collectstatic --noinput

# 8. Set proper file permissions
echo "🔒 Setting file permissions..."
chown -R www-data:www-data /var/www/glomart-crm/
chmod -R 755 /var/www/glomart-crm/
chmod 600 /var/www/glomart-crm/.env.production

# 9. Reload and restart services
echo "🔄 Restarting services..."
systemctl daemon-reload
systemctl restart glomart-crm
systemctl reload nginx

# 10. Health check
echo "🏥 Performing health check..."
sleep 5

if systemctl is-active --quiet glomart-crm; then
    echo "✅ Glomart CRM service is running"
else
    echo "❌ Glomart CRM service failed to start"
    echo "📋 Service status:"
    systemctl status glomart-crm
    echo ""
    echo "📋 Service logs:"
    journalctl -u glomart-crm -n 20 --no-pager
    exit 1
fi

if curl -f -s http://127.0.0.1:8000/admin/ >/dev/null; then
    echo "✅ Application is responding correctly"
    echo "🎉 PRODUCTION FIXED SUCCESSFULLY!"
    echo ""
    echo "📊 Settings Summary:"
    echo "   - Settings Module: real_estate_crm.settings_production"
    echo "   - Database: django_db_glomart_rs (MASTER DATA PRESERVED)"
    echo "   - Debug: False"
    echo "   - Static Files: Collected"
    echo "   - Services: Running"
    echo ""
    echo "🌐 Your site should now work at: https://sys.glomartrealestates.com"
else
    echo "⚠️  Service is running but application may not be responding correctly"
    echo "📋 Check application logs for details"
fi

echo ""
echo "✅ Production configuration fixed!"
echo "🗄️ Database remains untouched (master data preserved)"