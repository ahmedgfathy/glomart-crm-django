#!/bin/bash
# Production Deployment Script for MariaDB Fix
# This script updates settings.py on production server and restarts the service

echo "🚀 Deploying MariaDB fix to production server..."
echo "=========================================="

# Production server details
SERVER="root@sys.glomartrealestates.com"
REMOTE_PATH="/var/www/glomart-crm"
LOCAL_SETTINGS="real_estate_crm/settings.py"
REMOTE_SETTINGS="$REMOTE_PATH/real_estate_crm/settings.py"

echo "1. Backing up current settings on server..."
ssh $SERVER "cp $REMOTE_SETTINGS ${REMOTE_SETTINGS}.backup_$(date +%Y%m%d_%H%M%S)"

echo "2. Uploading updated settings.py..."
scp $LOCAL_SETTINGS $SERVER:$REMOTE_SETTINGS

echo "3. Verifying upload..."
ssh $SERVER "ls -la $REMOTE_SETTINGS"

echo "4. Testing database connection on server..."
ssh $SERVER "cd $REMOTE_PATH && source venv/bin/activate && python manage.py check --database default"

if [ $? -eq 0 ]; then
    echo "✅ Database connection test passed!"
    
    echo "5. Restarting Django service..."
    ssh $SERVER "systemctl restart glomart-crm"
    
    echo "6. Checking service status..."
    ssh $SERVER "systemctl status glomart-crm --no-pager"
    
    echo "7. Testing website..."
    echo "🌐 Please check: https://sys.glomartrealestates.com/dashboard/"
    
    echo "✅ Deployment complete!"
else
    echo "❌ Database connection test failed!"
    echo "Restoring backup settings..."
    ssh $SERVER "cp ${REMOTE_SETTINGS}.backup_* $REMOTE_SETTINGS"
    
    echo "🔧 Manual fix required:"
    echo "1. SSH to server: ssh $SERVER"
    echo "2. Check MariaDB: systemctl status mariadb"
    echo "3. Test connection: mysql -u root -p"
    echo "4. Use password: ZeroCall20!@HH##1655&&"
fi