#!/bin/bash

# 🚀 Production Database Clone Script for Glomart CRM
# This script safely clones the production database to your local MariaDB
# Production: 5.180.148.92 (sys.glomartrealestates.com)
# Local: localhost with root/zerocall

set -e  # Exit on any error

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_SERVER="5.180.148.92"
PRODUCTION_USER="root"
PRODUCTION_DB="django_db_glomart_rs"
LOCAL_USER="root"
LOCAL_PASSWORD="zerocall"
LOCAL_DB="django_db_glomart_rs"
BACKUP_DIR="./database_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="production_backup_${TIMESTAMP}.sql"

echo -e "${BLUE}🚀 Glomart CRM Production Database Clone${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo -e "  Production Server: ${PRODUCTION_SERVER}"
echo -e "  Production Database: ${PRODUCTION_DB}"
echo -e "  Local Database: ${LOCAL_DB}"
echo -e "  Backup Directory: ${BACKUP_DIR}"
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

# Create production database dump
echo -e "${YELLOW}📤 Creating production database dump...${NC}"
echo -e "  This may take a few minutes depending on database size..."

ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "
    echo '🔍 Checking production database...'
    if mysql -e 'USE $PRODUCTION_DB; SELECT COUNT(*) as tables FROM information_schema.tables WHERE table_schema=\"$PRODUCTION_DB\";' 2>/dev/null; then
        echo '✅ Production database accessible'
        echo '📊 Creating comprehensive database dump...'
        
        # Create dump with complete data, triggers, routines, and events
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
            '$PRODUCTION_DB' > /tmp/production_dump.sql
        
        echo '✅ Database dump created successfully'
        echo '📏 Dump file size:'
        ls -lh /tmp/production_dump.sql
    else
        echo '❌ Cannot access production database'
        exit 1
    fi
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Production database dump created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create production database dump${NC}"
    exit 1
fi
echo ""

# Download the dump file
echo -e "${YELLOW}⬇️  Downloading database dump to local machine...${NC}"
scp "$PRODUCTION_USER@$PRODUCTION_SERVER:/tmp/production_dump.sql" "${BACKUP_DIR}/${BACKUP_FILE}"

if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    echo -e "${GREEN}✅ Database dump downloaded successfully${NC}"
    echo -e "  File: ${BACKUP_DIR}/${BACKUP_FILE}"
    echo -e "  Size: $(ls -lh "${BACKUP_DIR}/${BACKUP_FILE}" | awk '{print $5}')"
else
    echo -e "${RED}❌ Failed to download database dump${NC}"
    exit 1
fi
echo ""

# Clean up remote dump file
echo -e "${YELLOW}🧹 Cleaning up remote dump file...${NC}"
ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" "rm -f /tmp/production_dump.sql"
echo -e "${GREEN}✅ Remote cleanup completed${NC}"
echo ""

# Backup existing local database if it exists
echo -e "${YELLOW}💾 Backing up existing local database (if exists)...${NC}"
if mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -e "USE $LOCAL_DB;" 2>/dev/null; then
    echo -e "  📋 Local database exists, creating backup..."
    mysqldump -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        "$LOCAL_DB" > "${BACKUP_DIR}/local_backup_${TIMESTAMP}.sql"
    echo -e "${GREEN}✅ Local database backed up to: ${BACKUP_DIR}/local_backup_${TIMESTAMP}.sql${NC}"
else
    echo -e "  📋 No existing local database found, proceeding..."
fi
echo ""

# Create/recreate local database
echo -e "${YELLOW}🗄️  Setting up local database...${NC}"
mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -e "
    DROP DATABASE IF EXISTS \`$LOCAL_DB\`;
    CREATE DATABASE \`$LOCAL_DB\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    GRANT ALL PRIVILEGES ON \`$LOCAL_DB\`.* TO '$LOCAL_USER'@'localhost';
    FLUSH PRIVILEGES;
"
echo -e "${GREEN}✅ Local database created: $LOCAL_DB${NC}"
echo ""

# Import production data
echo -e "${YELLOW}📥 Importing production data into local database...${NC}"
echo -e "  This may take several minutes depending on data size..."

# Show progress during import
mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" < "${BACKUP_DIR}/${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Production data imported successfully${NC}"
else
    echo -e "${RED}❌ Failed to import production data${NC}"
    exit 1
fi
echo ""

# Verify the import
echo -e "${YELLOW}🔍 Verifying database import...${NC}"
TABLE_COUNT=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
    USE $LOCAL_DB;
    SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$LOCAL_DB';
")

PROPERTY_COUNT=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
    USE $LOCAL_DB;
    SELECT COUNT(*) FROM properties_property;
" 2>/dev/null || echo "0")

LEAD_COUNT=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
    USE $LOCAL_DB;
    SELECT COUNT(*) FROM leads_lead;
" 2>/dev/null || echo "0")

USER_COUNT=$(mysql -u"$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "
    USE $LOCAL_DB;
    SELECT COUNT(*) FROM auth_user;
" 2>/dev/null || echo "0")

echo -e "${GREEN}📊 Import Verification Results:${NC}"
echo -e "  📋 Total Tables: $TABLE_COUNT"
echo -e "  🏠 Properties: $PROPERTY_COUNT"
echo -e "  👥 Leads: $LEAD_COUNT"
echo -e "  👤 Users: $USER_COUNT"
echo ""

# Update Django settings recommendation
echo -e "${YELLOW}⚙️  Next Steps for Local Development:${NC}"
echo ""
echo -e "${BLUE}1. Update your Django settings:${NC}"
echo -e "   Edit real_estate_crm/settings.py:"
echo -e "   DATABASES = {"
echo -e "       'default': {"
echo -e "           'ENGINE': 'django.db.backends.mysql',"
echo -e "           'NAME': '$LOCAL_DB',"
echo -e "           'HOST': 'localhost',"
echo -e "           'USER': '$LOCAL_USER',"
echo -e "           'PASSWORD': '$LOCAL_PASSWORD',"
echo -e "           'OPTIONS': {"
echo -e "               'charset': 'utf8mb4',"
echo -e "           },"
echo -e "       }"
echo -e "   }"
echo ""
echo -e "${BLUE}2. Install MySQL client for Python:${NC}"
echo -e "   pip install mysqlclient"
echo ""
echo -e "${BLUE}3. Test your local setup:${NC}"
echo -e "   python manage.py migrate --fake-initial"
echo -e "   python manage.py runserver"
echo ""
echo -e "${BLUE}4. Access your local CRM:${NC}"
echo -e "   http://localhost:8000"
echo ""

# Summary
echo -e "${GREEN}🎉 SUCCESS! Production database cloned successfully${NC}"
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}✅ Production dump: ${BACKUP_DIR}/${BACKUP_FILE}${NC}"
echo -e "${GREEN}✅ Local database: $LOCAL_DB ready for development${NC}"
echo -e "${GREEN}✅ All production data preserved in local environment${NC}"
echo ""
echo -e "${YELLOW}💡 Backup files location: ${BACKUP_DIR}/${NC}"
echo -e "${YELLOW}💡 You can now safely develop locally with full production data${NC}"
echo ""

# Create a settings update script
cat > update_local_settings.py << 'EOF'
#!/usr/bin/env python3
"""
Update Django settings for local development with production data
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
    
    # Database configuration for local development
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
    # MariaDB connection for owner databases
    'mariadb_owner': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'zerocall',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}'''
    
    # Replace the DATABASES configuration
    pattern = r'DATABASES\s*=\s*\{[^}]*\}[^}]*\}'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_db_config, content, flags=re.DOTALL)
        
        with open(settings_file, 'w') as f:
            f.write(content)
        
        print("✅ Django settings updated for local development")
        print("✅ Database configured to use local MariaDB with production data")
    else:
        print("❌ Could not find DATABASES configuration in settings.py")
        print("💡 Please update manually with the provided configuration")

if __name__ == '__main__':
    update_settings()
EOF

chmod +x update_local_settings.py
echo -e "${BLUE}📝 Created update_local_settings.py script${NC}"
echo -e "${YELLOW}   Run: python update_local_settings.py${NC}"
echo ""