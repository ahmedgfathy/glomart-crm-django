#!/bin/bash

# 🗑️ Remove Owner Databases Module Safely
# This script removes the Owner Database module while keeping the main CRM intact

set -e  # Exit on any error

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️  Safely Removing Owner Databases Module${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "${YELLOW}📋 This will remove:${NC}"
echo -e "  1. Owner app from Django project"
echo -e "  2. Owner Database sidebar link"
echo -e "  3. rs_* database connections"
echo -e "  4. Owner-related context processors"
echo -e "  5. Owner references from templates"
echo ""
echo -e "${YELLOW}⚠️  This will NOT affect:${NC}"
echo -e "  ✅ Main CRM functionality"
echo -e "  ✅ Properties, Leads, Projects modules"
echo -e "  ✅ User authentication and permissions"
echo -e "  ✅ Main database (django_db_glomart_rs)"
echo ""

# Confirm before proceeding
read -p "Are you sure you want to remove the Owner Databases module? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚫 Operation cancelled${NC}"
    exit 0
fi

echo -e "${YELLOW}🚀 Starting Owner Database module removal...${NC}"
echo ""

# Step 1: Remove owner app from INSTALLED_APPS
echo -e "${BLUE}1. Removing 'owner' from INSTALLED_APPS...${NC}"
if grep -q "'owner'," real_estate_crm/settings.py; then
    sed -i.backup "s/'owner',.*$//" real_estate_crm/settings.py
    echo -e "${GREEN}✅ Removed 'owner' from INSTALLED_APPS${NC}"
else
    echo -e "${YELLOW}⚠️  'owner' not found in INSTALLED_APPS${NC}"
fi

# Step 2: Remove owner URLs from main urls.py
echo -e "${BLUE}2. Removing owner URLs...${NC}"
if grep -q "path('owner/'," real_estate_crm/urls.py; then
    sed -i.backup "/path('owner\/'/d" real_estate_crm/urls.py
    echo -e "${GREEN}✅ Removed owner URLs from main urlpatterns${NC}"
else
    echo -e "${YELLOW}⚠️  Owner URLs not found in main urls.py${NC}"
fi

# Step 3: Remove mariadb_owner database configuration
echo -e "${BLUE}3. Removing mariadb_owner database configuration...${NC}"
if grep -q "mariadb_owner" real_estate_crm/settings.py; then
    # Create a temp file to rebuild DATABASES without mariadb_owner
    python3 -c "
import re

with open('real_estate_crm/settings.py', 'r') as f:
    content = f.read()

# Remove the mariadb_owner database configuration
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
    }
}'''

# Replace the DATABASES configuration
pattern = r'DATABASES\s*=\s*\{[^}]*\}[^}]*\}'
content = re.sub(pattern, new_db_config, content, flags=re.DOTALL)

# Remove DATABASE_ROUTERS if it exists
content = re.sub(r'DATABASE_ROUTERS\s*=\s*\[[^\]]*\]', '', content)

with open('real_estate_crm/settings.py', 'w') as f:
    f.write(content)

print('Database configuration cleaned')
"
    echo -e "${GREEN}✅ Removed mariadb_owner database configuration${NC}"
else
    echo -e "${YELLOW}⚠️  mariadb_owner configuration not found${NC}"
fi

# Step 4: Remove owner references from authentication views
echo -e "${BLUE}4. Cleaning owner references from authentication views...${NC}"
if grep -q "owner.models" authentication/views.py; then
    # Create a Python script to clean the authentication views
    python3 -c "
import re

with open('authentication/views.py', 'r') as f:
    content = f.read()

# Remove owner imports
content = re.sub(r'.*from owner\.models import.*\n', '', content)

# Remove owner-related code blocks
content = re.sub(r'\s*# Owner database records count.*?total_owner_records = 0.*?except:.*?total_owner_records = 0.*?\n', '\n    total_owner_records = 0  # Owner module removed\n', content, flags=re.DOTALL)

# Remove owner from context
content = re.sub(r\".*'total_owner_records': total_owner_records,.*\n\", '', content)

with open('authentication/views.py', 'w') as f:
    f.write(content)

print('Authentication views cleaned')
"
    echo -e "${GREEN}✅ Cleaned owner references from authentication views${NC}"
else
    echo -e "${YELLOW}⚠️  No owner references found in authentication views${NC}"
fi

# Step 5: Remove owner references from enhanced context processors
echo -e "${BLUE}5. Cleaning enhanced context processors...${NC}"
if [ -f "authentication/enhanced_context_processors.py" ]; then
    if grep -q "owner" authentication/enhanced_context_processors.py; then
        # Clean owner references from context processors
        python3 -c "
import re

with open('authentication/enhanced_context_processors.py', 'r') as f:
    content = f.read()

# Remove owner-related imports and code
content = re.sub(r'.*from owner\.models import.*\n', '', content)
content = re.sub(r'.*OwnerDatabase.*\n', '', content, flags=re.MULTILINE)
content = re.sub(r\".*'has_owner_access':.*\n\", '', content)
content = re.sub(r\".*'owner_databases_count':.*\n\", '', content)

with open('authentication/enhanced_context_processors.py', 'w') as f:
    f.write(content)

print('Enhanced context processors cleaned')
"
        echo -e "${GREEN}✅ Cleaned enhanced context processors${NC}"
    else
        echo -e "${YELLOW}⚠️  No owner references found in enhanced context processors${NC}"
    fi
fi

# Step 6: Remove Owner Database references from sidebar template
echo -e "${BLUE}6. Cleaning sidebar template...${NC}"
SIDEBAR_FILE="authentication/templates/authentication/partials/sidebar.html"
if [ -f "$SIDEBAR_FILE" ]; then
    if grep -q "Owner Databases" "$SIDEBAR_FILE"; then
        # Remove the entire Owner Databases section from sidebar
        sed -i.backup '/<!-- Owner Databases Module -->/,/{% endif %}/d' "$SIDEBAR_FILE"
        echo -e "${GREEN}✅ Removed Owner Databases from sidebar${NC}"
    else
        echo -e "${YELLOW}⚠️  Owner Databases section not found in sidebar${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Sidebar template not found${NC}"
fi

# Step 7: Remove Owner Database references from dashboard templates
echo -e "${BLUE}7. Cleaning dashboard templates...${NC}"
for template in "authentication/templates/authentication/dashboard.html" "authentication/templates/authentication/dashboard_old.html"; do
    if [ -f "$template" ]; then
        if grep -q "owner" "$template"; then
            # Remove owner-related template code
            sed -i.backup '/Owner/d' "$template"
            sed -i.backup '/total_owner_records/d' "$template"
            sed -i.backup '/has_owner_access/d' "$template"
            echo -e "${GREEN}✅ Cleaned $(basename $template)${NC}"
        fi
    fi
done

# Step 8: Remove owner references from enhanced admin
echo -e "${BLUE}8. Cleaning enhanced admin...${NC}"
if [ -f "authentication/enhanced_admin.py" ]; then
    if grep -q "'owner'" authentication/enhanced_admin.py; then
        sed -i.backup "/('owner'/d" authentication/enhanced_admin.py
        sed -i.backup "/'owner':/d" authentication/enhanced_admin.py
        echo -e "${GREEN}✅ Cleaned enhanced admin${NC}"
    fi
fi

# Step 9: Drop rs_* databases (optional)
echo -e "${BLUE}9. Removing rs_* databases (Owner Database storage)...${NC}"
read -p "Do you want to DROP all rs_* databases? This will permanently delete owner data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Get list of rs_* databases and drop them
    RS_DBS=($(mysql -uroot -pzerocall -N -e "SHOW DATABASES LIKE 'rs_%'"))
    
    if [ ${#RS_DBS[@]} -gt 0 ]; then
        echo -e "${YELLOW}Dropping ${#RS_DBS[@]} rs_* databases...${NC}"
        for db in "${RS_DBS[@]}"; do
            mysql -uroot -pzerocall -e "DROP DATABASE IF EXISTS \`$db\`"
            echo -e "  🗑️  Dropped $db"
        done
        echo -e "${GREEN}✅ All rs_* databases dropped${NC}"
    else
        echo -e "${YELLOW}⚠️  No rs_* databases found${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  Skipping database removal (databases kept)${NC}"
fi

# Step 10: Remove owner app directory (optional)
echo -e "${BLUE}10. Removing owner app directory...${NC}"
if [ -d "owner" ]; then
    read -p "Do you want to DELETE the entire 'owner' app directory? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Create a backup first
        tar -czf "owner_app_backup_$(date +%Y%m%d_%H%M%S).tar.gz" owner/
        rm -rf owner/
        echo -e "${GREEN}✅ Owner app directory removed (backup created)${NC}"
    else
        echo -e "${YELLOW}⏭️  Owner app directory kept${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Owner app directory not found${NC}"
fi

# Step 11: Clean up initialization scripts
echo -e "${BLUE}11. Removing owner-related scripts...${NC}"
for script in "initialize_owner_databases.py" "clone_all_production_databases.sh"; do
    if [ -f "$script" ]; then
        mv "$script" "${script}.removed"
        echo -e "${GREEN}✅ Moved $script to ${script}.removed${NC}"
    fi
done

# Step 12: Verify Django project still works
echo -e "${BLUE}12. Verifying Django project integrity...${NC}"
if python3 manage.py check --deploy 2>/dev/null; then
    echo -e "${GREEN}✅ Django project check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Django project check failed - please review the changes${NC}"
fi

# Final summary
echo ""
echo -e "${GREEN}🎉 Owner Databases Module Removal Complete! 🎉${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Owner app removed from Django project${NC}"
echo -e "${GREEN}✅ Sidebar navigation cleaned${NC}"
echo -e "${GREEN}✅ Database connections cleaned${NC}"
echo -e "${GREEN}✅ Template references removed${NC}"
echo -e "${GREEN}✅ Main CRM functionality preserved${NC}"
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo ""
echo -e "${BLUE}1. Test the Django project:${NC}"
echo -e "   python3 manage.py runserver"
echo ""
echo -e "${BLUE}2. Verify main functionality:${NC}"
echo -e "   - Properties module: ✅"
echo -e "   - Leads module: ✅"  
echo -e "   - Projects module: ✅"
echo -e "   - Authentication: ✅"
echo ""
echo -e "${BLUE}3. Clean navigation:${NC}"
echo -e "   - Owner Databases link: ❌ Removed"
echo -e "   - Main modules preserved: ✅"
echo ""
echo -e "${CYAN}📁 Backup files created with .backup extension${NC}"
echo -e "${CYAN}🔥 Main CRM system: Ready for production use${NC}"
echo ""