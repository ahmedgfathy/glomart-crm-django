#!/bin/bash

# 🔥 Complete Production Database Clone Script for Glomart CRM
# This script clones ALL databases including Owner Databases (rs_*) from production
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

echo -e "${BLUE}🔥 COMPLETE Glomart CRM Production Database Clone${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""
echo -e "${YELLOW}📋 This script will clone:${NC}"
echo -e "  1. Main CRM Database: ${MAIN_PRODUCTION_DB}"
echo -e "  2. All Owner Databases (rs_*)"
echo -e "  3. Any other related databases"
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
    echo -e "${YELLOW}💡 You may need to run: ssh-copy-id $PRODUCTION_USER@$PRODUCTION_SERVER${NC}"
    exit 1
fi
echo ""

# Get list of all databases from production
echo -e "${YELLOW}🔍 Discovering all databases on production server...${NC}"

# Create a temporary script to run on production server
ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "
cat > /tmp/get_databases.sql << 'EOF'
SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA 
WHERE SCHEMA_NAME NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys', 'phpmyadmin')
AND SCHEMA_NAME NOT LIKE 'roundcube%'
AND SCHEMA_NAME NOT LIKE 'postfix%'
AND SCHEMA_NAME NOT LIKE 'amavis%'
AND SCHEMA_NAME NOT LIKE 'iredadmin%'
AND SCHEMA_NAME NOT LIKE 'iredapd%'
AND SCHEMA_NAME NOT LIKE 'vmail%'
ORDER BY SCHEMA_NAME;
EOF

echo '📊 Production databases found:'
mysql -N -e 'source /tmp/get_databases.sql' > /tmp/database_list.txt
cat /tmp/database_list.txt
rm /tmp/get_databases.sql
"

# Download the database list
scp "$PRODUCTION_USER@$PRODUCTION_SERVER:/tmp/database_list.txt" "${BACKUP_DIR}/production_databases.txt"

# Read the database list
DATABASES=($(cat "${BACKUP_DIR}/production_databases.txt"))
echo -e "${GREEN}✅ Found ${#DATABASES[@]} databases to clone${NC}"
echo ""

# Show what we found
echo -e "${CYAN}📋 Databases to be cloned:${NC}"
MAIN_DBS=()
OWNER_DBS=()
OTHER_DBS=()

for db in "${DATABASES[@]}"; do
    if [[ "$db" == "$MAIN_PRODUCTION_DB" ]]; then
        MAIN_DBS+=("$db")
        echo -e "  🏢 ${GREEN}$db${NC} (Main CRM)"
    elif [[ "$db" == rs_* ]]; then
        OWNER_DBS+=("$db")
        echo -e "  🏠 ${YELLOW}$db${NC} (Owner Database)"
    else
        OTHER_DBS+=("$db")
        echo -e "  📦 ${BLUE}$db${NC} (Other)"
    fi
done

echo ""
echo -e "${CYAN}📊 Summary:${NC}"
echo -e "  Main CRM Databases: ${#MAIN_DBS[@]}"
echo -e "  Owner Databases (rs_*): ${#OWNER_DBS[@]}"
echo -e "  Other Databases: ${#OTHER_DBS[@]}"
echo -e "  ${GREEN}Total: ${#DATABASES[@]} databases${NC}"
echo ""

# Confirm before proceeding
read -p "Do you want to proceed with cloning all these databases? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚫 Operation cancelled by user${NC}"
    exit 0
fi

# Function to clone a single database
clone_database() {
    local db_name="$1"
    local db_type="$2"
    
    echo -e "${YELLOW}📤 Cloning database: ${CYAN}$db_name${NC} ($db_type)"
    
    # Create dump on production server
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "
        echo '🔍 Creating dump for $db_name...'
        
        # Check if database exists and has tables
        table_count=\$(mysql -N -e \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$db_name'\")
        
        if [ \"\$table_count\" -gt 0 ]; then
            echo '📊 Database has \$table_count tables, creating dump...'
            
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
                --set-gtid-purged=OFF \\
                '$db_name' > /tmp/${db_name}_dump.sql
            
            echo '✅ Dump created successfully for $db_name'
            ls -lh /tmp/${db_name}_dump.sql
        else
            echo '⚠️  Database $db_name is empty, creating minimal dump...'
            mysqldump --no-data '$db_name' > /tmp/${db_name}_dump.sql
        fi
    "
    
    # Download the dump
    echo -e "  ⬇️  Downloading $db_name dump..."
    scp "$PRODUCTION_USER@$PRODUCTION_SERVER:/tmp/${db_name}_dump.sql" "${BACKUP_DIR}/${db_name}_${TIMESTAMP}.sql"
    
    # Create/recreate local database
    echo -e "  🗄️  Setting up local database: $db_name"
    mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -e "
        DROP DATABASE IF EXISTS \`$db_name\`;
        CREATE DATABASE \`$db_name\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        GRANT ALL PRIVILEGES ON \`$db_name\`.* TO '$LOCAL_USER'@'localhost';
        FLUSH PRIVILEGES;
    "
    
    # Import the dump
    echo -e "  📥 Importing $db_name data..."
    mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" "$db_name" < "${BACKUP_DIR}/${db_name}_${TIMESTAMP}.sql"
    
    # Verify import
    local record_count=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema='$db_name'
    ")
    
    echo -e "  ${GREEN}✅ $db_name imported successfully (${record_count} tables)${NC}"
    
    # Cleanup remote dump
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "rm -f /tmp/${db_name}_dump.sql"
    
    return 0
}

# Clone Main CRM Database first
echo -e "${BLUE}🏢 STEP 1: Cloning Main CRM Database${NC}"
echo -e "${BLUE}=================================${NC}"
for db in "${MAIN_DBS[@]}"; do
    clone_database "$db" "Main CRM"
done
echo ""

# Clone Owner Databases
if [ ${#OWNER_DBS[@]} -gt 0 ]; then
    echo -e "${BLUE}🏠 STEP 2: Cloning Owner Databases${NC}"
    echo -e "${BLUE}================================${NC}"
    for db in "${OWNER_DBS[@]}"; do
        clone_database "$db" "Owner Database"
    done
    echo ""
fi

# Clone Other Databases
if [ ${#OTHER_DBS[@]} -gt 0 ]; then
    echo -e "${BLUE}📦 STEP 3: Cloning Other Databases${NC}"
    echo -e "${BLUE}=================================${NC}"
    for db in "${OTHER_DBS[@]}"; do
        clone_database "$db" "Other"
    done
    echo ""
fi

# Cleanup remote temporary files
echo -e "${YELLOW}🧹 Cleaning up remote temporary files...${NC}"
ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "rm -f /tmp/database_list.txt"

# Verify all databases locally
echo -e "${YELLOW}🔍 Verifying local databases...${NC}"
LOCAL_DBS=($(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
    SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA 
    WHERE SCHEMA_NAME NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
    ORDER BY SCHEMA_NAME;
"))

echo -e "${GREEN}📊 Local Database Verification:${NC}"
main_count=0
owner_count=0
other_count=0

for db in "${LOCAL_DBS[@]}"; do
    table_count=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
        SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$db'
    ")
    
    if [[ "$db" == "$MAIN_PRODUCTION_DB" ]]; then
        echo -e "  🏢 ${GREEN}$db${NC} ($table_count tables)"
        main_count=$((main_count + 1))
    elif [[ "$db" == rs_* ]]; then
        echo -e "  🏠 ${YELLOW}$db${NC} ($table_count tables)"
        owner_count=$((owner_count + 1))
    else
        echo -e "  📦 ${BLUE}$db${NC} ($table_count tables)"
        other_count=$((other_count + 1))
    fi
done

echo ""
echo -e "${GREEN}✅ Verification Summary:${NC}"
echo -e "  Main CRM Databases: $main_count"
echo -e "  Owner Databases: $owner_count"
echo -e "  Other Databases: $other_count"
echo -e "  ${GREEN}Total Local Databases: ${#LOCAL_DBS[@]}${NC}"

# Create comprehensive Django settings
echo -e "${YELLOW}⚙️  Creating comprehensive Django settings...${NC}"

cat > update_local_settings_complete.py << 'EOF'
#!/usr/bin/env python3
"""
Update Django settings for local development with ALL production databases
"""

import os
import re

def update_settings():
    settings_file = 'real_estate_crm/settings.py'
    
    if not os.path.exists(settings_file):
        print("❌ Settings file not found:", settings_file)
        return
    
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Database configuration for local development with all databases
    new_db_config = '''DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'zerocall',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    },
    # MariaDB connection for owner databases (rs_* databases)
    'mariadb_owner': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'zerocall',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Database router for owner databases
DATABASE_ROUTERS = ['owner.routers.OwnerDatabaseRouter']'''
    
    # Replace the DATABASES configuration
    pattern = r'DATABASES\s*=\s*\{[^}]*\}[^}]*\}'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_db_config, content, flags=re.DOTALL)
        
        with open(settings_file, 'w') as f:
            f.write(content)
        
        print("✅ Django settings updated for complete local development")
        print("✅ All databases (main + owner) configured")
        print("✅ Database router added for owner databases")
    else:
        print("❌ Could not find DATABASES configuration in settings.py")
        print("💡 Please update manually with the provided configuration")

if __name__ == '__main__':
    update_settings()
EOF

chmod +x update_local_settings_complete.py
python3 update_local_settings_complete.py

# Create owner database initialization script
cat > initialize_owner_databases.py << 'EOF'
#!/usr/bin/env python3
"""
Initialize Owner Database records in Django for all cloned rs_ databases
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from owner.models import OwnerDatabase
import pymysql

def initialize_owner_databases():
    print("🏠 Initializing Owner Database records...")
    
    try:
        # Get all rs_ databases from local MariaDB
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='zerocall',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE 'rs_%'")
            databases = cursor.fetchall()
            
        connection.close()
        
        if not databases:
            print("⚠️  No rs_ databases found in local MariaDB")
            return
        
        created_count = 0
        updated_count = 0
        
        # Database categories mapping
        db_categories = {
            'rehab': 'Real Estate - Major Developments',
            'marassi': 'Real Estate - Major Developments', 
            'mivida': 'Real Estate - Major Developments',
            'palm': 'Real Estate - Major Developments',
            'uptown': 'Real Estate - Compound Projects',
            'amwaj': 'Real Estate - Compound Projects',
            'gouna': 'Real Estate - Regional Projects',
            'mangroovy': 'Real Estate - Regional Projects',
            'sahel': 'Real Estate - Regional Projects',
            'katameya': 'Real Estate - New Cairo/Tagamoa',
            'sabour': 'Real Estate - New Cairo/Tagamoa',
            'tagamoa': 'Real Estate - New Cairo/Tagamoa',
            'zayed': 'Real Estate - 6th October/Zayed',
            'october': 'Real Estate - 6th October/Zayed',
            'villas': 'Real Estate - 6th October/Zayed',
            'sodic': 'Real Estate - SODIC Projects',
            'jedar': 'Real Estate - Other Developments',
            'hadaeq': 'Real Estate - Other Developments',
            'alexandria': 'Real Estate - Other Developments',
            'emaar': 'Real Estate - Commercial/Corporate',
            'vip': 'Real Estate - Commercial/Corporate',
            'customer': 'Real Estate - Commercial/Corporate',
            'mawasem': 'Real Estate - Commercial/Corporate',
            'sea_shell': 'Real Estate - Commercial/Corporate',
            'jaguar': 'Automotive',
            'jeep': 'Automotive',
        }
        
        for db_info in databases:
            db_name = db_info['Database']
            
            # Determine category
            category = 'Uncategorized'
            for keyword, cat in db_categories.items():
                if keyword in db_name.lower():
                    category = cat
                    break
            
            # Create or update database record
            db_obj, created = OwnerDatabase.objects.get_or_create(
                name=db_name,
                defaults={
                    'category': category,
                    'table_name': 'data',
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                print(f"  ✅ Created: {db_name} ({category})")
            else:
                # Update category if changed
                if db_obj.category != category:
                    db_obj.category = category
                    db_obj.save()
                    updated_count += 1
                    print(f"  📝 Updated: {db_name} ({category})")
            
            # Generate and set display name
            if not db_obj.display_name or db_obj.display_name == db_obj.name:
                db_obj.display_name = db_obj.generate_display_name()
                db_obj.save()
            
            # Update record count
            table_info = db_obj.get_table_info()
            if table_info:
                print(f"     📊 Records: {table_info['record_count']:,}")
        
        print(f"\n🎉 Owner Database initialization complete!")
        print(f"  ✅ Created: {created_count}")
        print(f"  📝 Updated: {updated_count}")
        print(f"  📊 Total Owner Databases: {len(databases)}")
        
    except Exception as e:
        print(f"❌ Error initializing owner databases: {e}")

if __name__ == '__main__':
    initialize_owner_databases()
EOF

chmod +x initialize_owner_databases.py

# Final summary
echo ""
echo -e "${GREEN}🎉 COMPLETE DATABASE CLONE SUCCESSFUL! 🎉${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✅ Main CRM Database: Cloned and ready${NC}"
echo -e "${GREEN}✅ Owner Databases (rs_*): ${owner_count} databases cloned${NC}"
echo -e "${GREEN}✅ Django settings: Updated for local development${NC}"
echo -e "${GREEN}✅ All production data: Available locally${NC}"
echo ""
echo -e "${YELLOW}🚀 Next Steps for Local Development:${NC}"
echo ""
echo -e "${BLUE}1. Install Python dependencies:${NC}"
echo -e "   pip install mysqlclient pymysql"
echo ""
echo -e "${BLUE}2. Initialize Owner Databases in Django:${NC}"
echo -e "   python initialize_owner_databases.py"
echo ""
echo -e "${BLUE}3. Run Django migrations:${NC}"
echo -e "   python manage.py migrate --fake-initial"
echo ""
echo -e "${BLUE}4. Start local development server:${NC}"
echo -e "   python manage.py runserver"
echo ""
echo -e "${BLUE}5. Access your complete local CRM:${NC}"
echo -e "   http://localhost:8000"
echo ""
echo -e "${CYAN}📁 Backup files location: ${BACKUP_DIR}${NC}"
echo -e "${CYAN}🏠 Owner Databases: Ready for use in sidebar${NC}"
echo -e "${CYAN}🔥 Full production environment: Replicated locally${NC}"
echo ""