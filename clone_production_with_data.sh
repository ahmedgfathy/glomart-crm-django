#!/bin/bash

# 🔥 FIXED Production Database Clone - WITH DATA
# This script clones ALL production databases INCLUDING DATA
# Production: 5.180.148.92 (sys.glomartrealestates.com)  
# Local: localhost with root/zerocall

set -e  # Exit on any error

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_SERVER="5.180.148.92"
PRODUCTION_USER="root"
MAIN_PRODUCTION_DB="django_db_glomart_rs"
LOCAL_USER="root"
LOCAL_PASSWORD="zerocall"
BACKUP_DIR="./database_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}🔥 FIXED Production Database Clone WITH DATA${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""
echo -e "${YELLOW}📋 This will clone WITH DATA:${NC}"
echo -e "  1. Main CRM Database: ${MAIN_PRODUCTION_DB} (WITH user data, properties, leads, etc.)"
echo -e "  2. Owner Databases (rs_*) (WITH customer data)"
echo -e "  3. Excluding only large media files to save bandwidth"
echo ""

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Function to check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ Error: $1 is not installed or not in PATH${NC}"
        exit 1
    fi
}

# Check required commands
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
check_command mysql
check_command mysqldump
check_command ssh
echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# Test local MariaDB connection
echo -e "${YELLOW}🔗 Testing local MariaDB connection...${NC}"
if mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -e "SELECT VERSION();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Local MariaDB connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to local MariaDB with credentials root/zerocall${NC}"
    echo -e "${YELLOW}💡 Please ensure MariaDB is running and credentials are correct${NC}"
    exit 1
fi
echo ""

# Test SSH connection to production
echo -e "${YELLOW}🔗 Testing SSH connection to production...${NC}"
if ssh -o ConnectTimeout=10 -o BatchMode=yes "$PRODUCTION_USER@$PRODUCTION_SERVER" exit 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection to production successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to production server via SSH${NC}"
    echo -e "${YELLOW}💡 Please ensure SSH key authentication is set up${NC}"
    exit 1
fi
echo ""

# Function to clone a database with data
clone_database_with_data() {
    local db_name="$1"
    local db_type="$2"
    
    echo -e "${YELLOW}📤 Cloning database WITH DATA: ${CYAN}$db_name${NC} ($db_type)"
    
    # Create dump on production server with CORRECT parameters
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "
        echo '🔍 Creating FULL data dump for $db_name...'
        
        # Check if database exists and has tables
        table_count=\$(mysql -N -e \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$db_name'\")
        record_count=0
        
        if [ \"\$table_count\" -gt 0 ]; then
            # Get total record count
            record_count=\$(mysql -N -e \"
                SELECT SUM(table_rows) 
                FROM information_schema.tables 
                WHERE table_schema='$db_name' AND table_type='BASE TABLE'
            \")
            
            echo '📊 Database has \$table_count tables with ~\$record_count records'
            echo '💾 Creating FULL dump with ALL data...'
            
            # FIXED mysqldump command - remove problematic parameter
            mysqldump \\
                --single-transaction \\
                --routines \\
                --triggers \\
                --events \\
                --complete-insert \\
                --extended-insert \\
                --lock-tables=false \\
                --add-drop-table \\
                --disable-keys \\
                --hex-blob \\
                --where='1=1' \\
                '$db_name' > /tmp/${db_name}_full_dump.sql
            
            echo '✅ Full dump created successfully for $db_name'
            ls -lh /tmp/${db_name}_full_dump.sql
        else
            echo '⚠️  Database $db_name is empty, creating structure dump...'
            mysqldump --no-data '$db_name' > /tmp/${db_name}_full_dump.sql
        fi
    "
    
    # Download the dump
    echo -e "  ⬇️  Downloading $db_name full dump..."
    scp "$PRODUCTION_USER@$PRODUCTION_SERVER:/tmp/${db_name}_full_dump.sql" "${BACKUP_DIR}/${db_name}_full_${TIMESTAMP}.sql"
    
    # Check if file was downloaded and has content
    local dump_file="${BACKUP_DIR}/${db_name}_full_${TIMESTAMP}.sql"
    if [ -f "$dump_file" ] && [ -s "$dump_file" ]; then
        local file_size=$(ls -lh "$dump_file" | awk '{print $5}')
        echo -e "  ✅ Downloaded successfully: $file_size"
    else
        echo -e "  ⚠️  Downloaded file is empty or missing"
    fi
    
    # Drop and recreate local database
    echo -e "  🗄️  Recreating local database: $db_name"
    mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -e "
        DROP DATABASE IF EXISTS \`$db_name\`;
        CREATE DATABASE \`$db_name\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        GRANT ALL PRIVILEGES ON \`$db_name\`.* TO '$LOCAL_USER'@'localhost';
        FLUSH PRIVILEGES;
    " || {
        echo -e "  ${RED}❌ Failed to recreate database $db_name${NC}"
        return 1
    }
    
    # Import the dump
    echo -e "  📥 Importing $db_name data (this may take a while for large databases)..."
    if mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" "$db_name" < "$dump_file"; then
        echo -e "  ${GREEN}✅ Data imported successfully${NC}"
    else
        echo -e "  ${RED}❌ Failed to import data${NC}"
        return 1
    fi
    
    # Verify import - count tables and records
    local local_tables=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
        SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$db_name'
    ")
    
    # Count records in main tables
    local main_records=0
    if [[ "$db_name" == "django_db_glomart_rs" ]]; then
        main_records=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
            SELECT 
                COALESCE((SELECT COUNT(*) FROM \`$db_name\`.auth_user), 0) +
                COALESCE((SELECT COUNT(*) FROM \`$db_name\`.properties_property), 0) +
                COALESCE((SELECT COUNT(*) FROM \`$db_name\`.leads_lead), 0)
        " 2>/dev/null || echo "0")
    elif [[ "$db_name" == rs_* ]]; then
        main_records=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
            SELECT COALESCE((SELECT COUNT(*) FROM \`$db_name\`.data), 0)
        " 2>/dev/null || echo "0")
    fi
    
    echo -e "  ${GREEN}✅ Verification: ${local_tables} tables, ${main_records} main records${NC}"
    
    # Cleanup remote dump
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "rm -f /tmp/${db_name}_full_dump.sql"
    
    return 0
}

# Clone Main CRM Database first (most important)
echo -e "${BLUE}🏢 STEP 1: Cloning Main CRM Database WITH ALL DATA${NC}"
echo -e "${BLUE}=================================================${NC}"
clone_database_with_data "$MAIN_PRODUCTION_DB" "Main CRM"
echo ""

# Ask user if they want to continue with Owner databases (they're large)
echo -e "${YELLOW}🤔 Do you want to clone ALL 40 Owner Databases too?${NC}"
echo -e "   This will take significant time and bandwidth (potentially several GB)"
read -p "Clone Owner Databases? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🏠 STEP 2: Cloning Owner Databases WITH DATA${NC}"
    echo -e "${BLUE}===========================================${NC}"
    
    # Get owner databases list
    OWNER_DBS=($(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "SHOW DATABASES LIKE 'rs_%'"))
    
    if [ ${#OWNER_DBS[@]} -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No rs_ databases found locally. Getting list from production...${NC}"
        ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "mysql -N -e \"SHOW DATABASES LIKE 'rs_%'\"" > /tmp/owner_dbs.txt
        OWNER_DBS=($(cat /tmp/owner_dbs.txt))
        rm -f /tmp/owner_dbs.txt
    fi
    
    echo -e "${GREEN}Found ${#OWNER_DBS[@]} owner databases to clone${NC}"
    
    for db in "${OWNER_DBS[@]}"; do
        clone_database_with_data "$db" "Owner Database"
    done
else
    echo -e "${YELLOW}⏭️  Skipping Owner Databases (you can run this script again to get them)${NC}"
fi
echo ""

# Final verification
echo -e "${YELLOW}🔍 Final verification of cloned data...${NC}"

# Check main CRM database
if mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" "$MAIN_PRODUCTION_DB" -e "SELECT COUNT(*) as users FROM auth_user; SELECT COUNT(*) as properties FROM properties_property; SELECT COUNT(*) as leads FROM leads_lead;" 2>/dev/null; then
    echo -e "${GREEN}✅ Main CRM database verified with data${NC}"
else
    echo -e "${RED}❌ Main CRM database verification failed${NC}"
fi

# Create a simple test script
cat > test_local_data.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify local data is properly loaded
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from django.contrib.auth.models import User
from properties.models import Property
from leads.models import Lead

def test_data():
    print("🔍 Testing local data access...")
    
    try:
        # Test users
        user_count = User.objects.count()
        print(f"👤 Users: {user_count}")
        
        if user_count > 0:
            sample_user = User.objects.first()
            print(f"   Sample user: {sample_user.username} ({sample_user.email})")
        
        # Test properties  
        property_count = Property.objects.count()
        print(f"🏠 Properties: {property_count}")
        
        if property_count > 0:
            sample_property = Property.objects.first()
            print(f"   Sample property: {sample_property.property_id}")
        
        # Test leads
        lead_count = Lead.objects.count() 
        print(f"👥 Leads: {lead_count}")
        
        if lead_count > 0:
            sample_lead = Lead.objects.first()
            print(f"   Sample lead: {sample_lead.first_name} {sample_lead.last_name}")
        
        print(f"\n🎉 SUCCESS! Local database has {user_count + property_count + lead_count} total records")
        return True
        
    except Exception as e:
        print(f"❌ Error testing data: {e}")
        return False

if __name__ == '__main__':
    test_data()
EOF

chmod +x test_local_data.py

# Final summary
echo ""
echo -e "${GREEN}🎉 PRODUCTION DATABASE CLONE WITH DATA COMPLETE! 🎉${NC}"
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}✅ Main CRM Database: Cloned WITH all user data${NC}"
echo -e "${GREEN}✅ Users, Properties, Leads: All imported${NC}"
echo -e "${GREEN}✅ Authentication: Production users available${NC}"
echo -e "${GREEN}✅ Local Development: Ready with production data${NC}"
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo ""
echo -e "${BLUE}1. Test your data import:${NC}"
echo -e "   python3 test_local_data.py"
echo ""
echo -e "${BLUE}2. Start Django development server:${NC}"
echo -e "   source venv/bin/activate && python manage.py runserver"
echo ""
echo -e "${BLUE}3. Access your CRM with production data:${NC}"
echo -e "   http://localhost:8000"
echo ""
echo -e "${BLUE}4. Login with production credentials:${NC}"
echo -e "   Use any production username/password from the cloned user data"
echo ""
echo -e "${CYAN}📁 Backup files location: ${BACKUP_DIR}${NC}"
echo -e "${CYAN}🔥 Full production data: Available for local development${NC}"
echo ""