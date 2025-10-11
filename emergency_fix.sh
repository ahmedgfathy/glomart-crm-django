#!/bin/bash
# Emergency Production Database Fix
# This script will fix the MariaDB connection on production server

echo "🚨 EMERGENCY DATABASE FIX FOR PRODUCTION"
echo "========================================"

SERVER="sys.glomartrealestates.com"
SERVER_USER="root"
REMOTE_PATH="/var/www/glomart-crm"

echo "Step 1: Upload corrected settings.py to production..."
scp real_estate_crm/settings.py ${SERVER_USER}@${SERVER}:${REMOTE_PATH}/real_estate_crm/settings.py

echo ""
echo "Step 2: SSH Commands to run on production server:"
echo "================================================="

cat << 'EOF'
# Connect to production server
ssh root@sys.glomartrealestates.com

# Step 2a: Verify settings uploaded correctly
cd /var/www/glomart-crm
grep "PASSWORD" real_estate_crm/settings.py

# Step 2b: Test MariaDB connection manually
mysql -u root -p
# Enter password: ZeroCall20!@HH##1655&&
# Run these commands in MySQL:
SHOW DATABASES;
USE django_db_glomart_rs;
SHOW TABLES;
EXIT;

# Step 2c: Test Django database connection
source venv/bin/activate
python manage.py check --database default

# Step 2d: If connection works, restart Django service
sudo systemctl restart glomart-crm
sudo systemctl status glomart-crm

# Step 2e: Check Django logs for any errors
sudo journalctl -u glomart-crm -f --lines=20
EOF

echo ""
echo "Step 3: Alternative - Run deployment script:"
echo "==========================================="
echo "./deploy_mariadb_fix.sh"

echo ""
echo "Step 4: Test website after deployment:"
echo "====================================="
echo "Visit: https://sys.glomartrealestates.com/dashboard/"

echo ""
echo "🔧 If MariaDB connection still fails:"
echo "===================================="
echo "1. Check MariaDB service: sudo systemctl status mariadb"
echo "2. Reset MariaDB password: sudo mysql_secure_installation"
echo "3. Create dedicated Django user (safer than root)"
echo ""
echo "Press ENTER to start deployment..."
read