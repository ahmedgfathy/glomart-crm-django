#!/bin/bash
# Copy Production Database to Local Development
# This script helps you get ALL production data into your local database

set -e

echo "🗄️ COPYING PRODUCTION DATABASE TO LOCAL DEVELOPMENT"
echo "=================================================="
echo ""
echo "Production DB: django_db_glomart_rs (root/ZeroCall20!@HH##1655&&)"
echo "Local DB: glomart_crm_local (root/zerocall)"
echo ""

# Check if we're in the right directory
if [[ ! -f "manage.py" ]]; then
    echo "❌ Error: Run this script from the Django project root directory"
    exit 1
fi

# Method 1: Try SSH tunnel (if you have SSH access)
echo "🔗 Method 1: SSH Tunnel + Direct Copy"
echo "======================================"
echo ""
echo "If you have SSH access to the production server (5.180.148.92), run:"
echo ""
echo "# Step 1: Create SSH tunnel (in separate terminal)"
echo "ssh -L 3307:localhost:3306 username@5.180.148.92"
echo ""
echo "# Step 2: Then run this command (in this terminal):"
echo "mysqldump -h127.0.0.1 -P3307 -uroot -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs | mysql -hlocalhost -uroot -pzerocall glomart_crm_local"
echo ""
read -p "Do you want to try SSH tunnel method? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📋 Instructions:"
    echo "1. Open a NEW terminal window"
    echo "2. Run: ssh -L 3307:localhost:3306 username@5.180.148.92"
    echo "3. Keep that terminal open"
    echo "4. Come back here and press Enter when tunnel is ready"
    echo ""
    read -p "Press Enter when SSH tunnel is established..."
    
    echo "🔄 Attempting to copy database through SSH tunnel..."
    
    # Test tunnel connection
    if mysql -h127.0.0.1 -P3307 -uroot -p'ZeroCall20!@HH##1655&&' -e "SELECT 1;" >/dev/null 2>&1; then
        echo "✅ SSH tunnel connection successful!"
        
        # Backup local database first
        echo "💾 Backing up local database..."
        mysqldump -hlocalhost -uroot -pzerocall glomart_crm_local > "local_backup_$(date +%Y%m%d_%H%M%S).sql" 2>/dev/null || echo "⚠️ No local database to backup"
        
        # Drop and recreate local database
        echo "🗑️ Recreating local database..."
        mysql -hlocalhost -uroot -pzerocall -e "DROP DATABASE IF EXISTS glomart_crm_local;" 
        mysql -hlocalhost -uroot -pzerocall -e "CREATE DATABASE glomart_crm_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        
        # Copy production to local
        echo "📥 Copying production database to local..."
        mysqldump -h127.0.0.1 -P3307 -uroot -p'ZeroCall20!@HH##1655&&' --single-transaction django_db_glomart_rs | mysql -hlocalhost -uroot -pzerocall glomart_crm_local
        
        if [ $? -eq 0 ]; then
            echo "✅ SUCCESS! Production database copied to local!"
            
            # Get record counts
            echo ""
            echo "📊 Data Summary:"
            echo "Properties: $(mysql -hlocalhost -uroot -pzerocall glomart_crm_local -e "SELECT COUNT(*) FROM properties_property;" -s -N 2>/dev/null || echo "Table not found")"
            echo "Leads: $(mysql -hlocalhost -uroot -pzerocall glomart_crm_local -e "SELECT COUNT(*) FROM leads_lead;" -s -N 2>/dev/null || echo "Table not found")"
            echo "Projects: $(mysql -hlocalhost -uroot -pzerocall glomart_crm_local -e "SELECT COUNT(*) FROM projects_project;" -s -N 2>/dev/null || echo "Table not found")"
            echo "Users: $(mysql -hlocalhost -uroot -pzerocall glomart_crm_local -e "SELECT COUNT(*) FROM auth_user;" -s -N 2>/dev/null || echo "Table not found")"
            
            # Run migrations
            if [ -d "venv" ]; then
                echo ""
                echo "🔧 Running Django migrations..."
                source venv/bin/activate
                export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local
                python manage.py migrate --noinput
                echo "✅ Migrations completed!"
            fi
            
            echo ""
            echo "🎉 PRODUCTION DATABASE SUCCESSFULLY COPIED TO LOCAL!"
            echo "🚀 You can now run: python manage.py runserver"
            exit 0
        else
            echo "❌ Copy failed!"
        fi
    else
        echo "❌ Cannot connect through SSH tunnel"
    fi
fi

echo ""
echo "🔗 Method 2: Manual Export/Import"
echo "================================="
echo ""
echo "Since direct connection didn't work, here are the manual steps:"
echo ""
echo "📋 STEP 1: On Production Server (5.180.148.92)"
echo "-----------------------------------------------"
echo "SSH into your production server and run:"
echo ""
echo "mkdir -p /tmp/db_backup"
echo "mysqldump -uroot -p'ZeroCall20!@HH##1655&&' --single-transaction django_db_glomart_rs > /tmp/db_backup/production_full_$(date +%Y%m%d).sql"
echo "echo 'Export completed. File: /tmp/db_backup/production_full_$(date +%Y%m%d).sql'"
echo ""
echo "📋 STEP 2: Download to Your Mac"
echo "-------------------------------"
echo "From your local machine, run:"
echo ""
echo "scp username@5.180.148.92:/tmp/db_backup/production_full_*.sql ."
echo ""
echo "📋 STEP 3: Import to Local Database"
echo "-----------------------------------"
echo "Once you have the .sql file locally, run:"
echo ""
echo "# Recreate local database"
echo "mysql -hlocalhost -uroot -pzerocall -e 'DROP DATABASE IF EXISTS glomart_crm_local;'"
echo "mysql -hlocalhost -uroot -pzerocall -e 'CREATE DATABASE glomart_crm_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'"
echo ""
echo "# Import production data"
echo "mysql -hlocalhost -uroot -pzerocall glomart_crm_local < production_full_*.sql"
echo ""
echo "# Run Django migrations"
echo "source venv/bin/activate"
echo "export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local"
echo "python manage.py migrate"
echo ""

echo "🔗 Method 3: Quick Commands (Copy & Paste)"
echo "==========================================="
echo ""
echo "If you want to just copy and paste commands:"
echo ""
echo "1️⃣ On production server:"
cat << 'EOF'
mysqldump -uroot -p'ZeroCall20!@HH##1655&&' --single-transaction django_db_glomart_rs > /tmp/production_backup.sql && echo "✅ Export complete: /tmp/production_backup.sql"
EOF
echo ""
echo "2️⃣ Download file (replace 'username' with your SSH username):"
echo "scp username@5.180.148.92:/tmp/production_backup.sql ."
echo ""
echo "3️⃣ Import to local:"
cat << 'EOF'
mysql -hlocalhost -uroot -pzerocall -e "DROP DATABASE IF EXISTS glomart_crm_local; CREATE DATABASE glomart_crm_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" && mysql -hlocalhost -uroot -pzerocall glomart_crm_local < production_backup.sql && echo "✅ Import complete!"
EOF
echo ""

echo "🎯 Choose the method that works best for you!"
echo "All methods will copy the COMPLETE production database to your local environment."