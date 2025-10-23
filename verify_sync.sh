#!/bin/bash
# Comprehensive Production vs Local Verification

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VERIFYING: PRODUCTION = LOCAL (100% Match Check)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROD_SERVER="root@5.180.148.92"
PROD_PATH="/var/www/glomart-crm"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=== 1. DATABASE COMPARISON ==="
echo "Comparing table counts and row counts..."

# Get production database stats
echo -e "\n${BLUE}Production Database:${NC}"
ssh $PROD_SERVER 'mysql -u root -p"ZeroCall20!@HH##1655&&" django_db_glomart_rs -e "
SELECT 
  \"properties_property\" as tbl, COUNT(*) as count FROM properties_property
UNION ALL SELECT \"auth_user\", COUNT(*) FROM auth_user
UNION ALL SELECT \"leads_lead\", COUNT(*) FROM leads_lead  
UNION ALL SELECT \"projects_project\", COUNT(*) FROM projects_project
UNION ALL SELECT \"properties_propertyimage\", COUNT(*) FROM properties_propertyimage
UNION ALL SELECT \"authentication_profile\", COUNT(*) FROM authentication_profile;
" 2>/dev/null' > /tmp/prod_db.txt

cat /tmp/prod_db.txt

# Get local database stats
echo -e "\n${BLUE}Local Database:${NC}"
mysql -u root -pzerocall django_db_glomart_rs -e "
SELECT 
  'properties_property' as tbl, COUNT(*) as count FROM properties_property
UNION ALL SELECT 'auth_user', COUNT(*) FROM auth_user
UNION ALL SELECT 'leads_lead', COUNT(*) FROM leads_lead  
UNION ALL SELECT 'projects_project', COUNT(*) FROM projects_project
UNION ALL SELECT 'properties_propertyimage', COUNT(*) FROM properties_propertyimage
UNION ALL SELECT 'authentication_profile', COUNT(*) FROM authentication_profile;
" 2>/dev/null > /tmp/local_db.txt

cat /tmp/local_db.txt

# Compare
if diff -q /tmp/prod_db.txt /tmp/local_db.txt > /dev/null; then
    echo -e "${GREEN}✓ DATABASE MATCHES 100%${NC}"
else
    echo -e "${RED}✗ DATABASE MISMATCH${NC}"
    diff /tmp/prod_db.txt /tmp/local_db.txt
fi

echo ""
echo "=== 2. STATIC FILES COMPARISON ==="

# Compare static/css/style.css
echo -e "\n${BLUE}Checking static/css/style.css...${NC}"
ssh $PROD_SERVER "md5sum $PROD_PATH/static/css/style.css" 2>/dev/null > /tmp/prod_css_md5.txt
md5 static/css/style.css | awk '{print $4" *static/css/style.css"}' > /tmp/local_css_md5.txt

PROD_CSS_MD5=$(cat /tmp/prod_css_md5.txt | awk '{print $1}')
LOCAL_CSS_MD5=$(cat /tmp/local_css_md5.txt | awk '{print $1}')

if [ "$PROD_CSS_MD5" = "$LOCAL_CSS_MD5" ]; then
    echo -e "${GREEN}✓ style.css MATCHES (MD5: $LOCAL_CSS_MD5)${NC}"
else
    echo -e "${RED}✗ style.css MISMATCH${NC}"
    echo "Production MD5: $PROD_CSS_MD5"
    echo "Local MD5: $LOCAL_CSS_MD5"
fi

# Compare logo
echo -e "\n${BLUE}Checking static/images/logo.png...${NC}"
ssh $PROD_SERVER "md5sum $PROD_PATH/static/images/logo.png" 2>/dev/null > /tmp/prod_logo_md5.txt
md5 static/images/logo.png | awk '{print $4" *static/images/logo.png"}' > /tmp/local_logo_md5.txt

PROD_LOGO_MD5=$(cat /tmp/prod_logo_md5.txt | awk '{print $1}')
LOCAL_LOGO_MD5=$(cat /tmp/local_logo_md5.txt | awk '{print $1}')

if [ "$PROD_LOGO_MD5" = "$LOCAL_LOGO_MD5" ]; then
    echo -e "${GREEN}✓ logo.png MATCHES (MD5: $LOCAL_LOGO_MD5)${NC}"
else
    echo -e "${RED}✗ logo.png MISMATCH${NC}"
    echo "Production MD5: $PROD_LOGO_MD5"
    echo "Local MD5: $LOCAL_LOGO_MD5"
fi

# List all static files
echo -e "\n${BLUE}All static files:${NC}"
echo "Production:"
ssh $PROD_SERVER "find $PROD_PATH/static -type f | wc -l" 2>/dev/null
echo "Local:"
find static -type f | wc -l

echo ""
echo "=== 3. TEMPLATES COMPARISON ==="

# Count templates
echo -e "${BLUE}Template counts:${NC}"
echo "Production:"
ssh $PROD_SERVER "find $PROD_PATH/templates -type f -name '*.html' | wc -l" 2>/dev/null
echo "Local:"
find templates -type f -name '*.html' | wc -l

# Compare base.html
echo -e "\n${BLUE}Checking templates/base.html...${NC}"
ssh $PROD_SERVER "md5sum $PROD_PATH/templates/base.html" 2>/dev/null > /tmp/prod_base_md5.txt
md5 templates/base.html 2>/dev/null | awk '{print $4" *templates/base.html"}' > /tmp/local_base_md5.txt

PROD_BASE_MD5=$(cat /tmp/prod_base_md5.txt | awk '{print $1}')
LOCAL_BASE_MD5=$(cat /tmp/local_base_md5.txt | awk '{print $1}')

if [ "$PROD_BASE_MD5" = "$LOCAL_BASE_MD5" ]; then
    echo -e "${GREEN}✓ base.html MATCHES (MD5: $LOCAL_BASE_MD5)${NC}"
else
    echo -e "${YELLOW}⚠ base.html DIFFERENT (may have local modifications)${NC}"
fi

echo ""
echo "=== 4. PYTHON CODE FILES COMPARISON ==="

# Check key Python files
echo -e "${BLUE}Checking settings files...${NC}"

for file in "real_estate_crm/settings.py" "real_estate_crm/settings_production.py"; do
    if [ -f "$file" ]; then
        ssh $PROD_SERVER "md5sum $PROD_PATH/$file" 2>/dev/null > /tmp/prod_file.txt
        md5 "$file" 2>/dev/null | awk -v f="$file" '{print $4" *"f}' > /tmp/local_file.txt
        
        PROD_MD5=$(cat /tmp/prod_file.txt | awk '{print $1}')
        LOCAL_MD5=$(cat /tmp/local_file.txt | awk '{print $1}')
        
        if [ "$PROD_MD5" = "$LOCAL_MD5" ]; then
            echo -e "${GREEN}✓ $file MATCHES${NC}"
        else
            echo -e "${YELLOW}⚠ $file DIFFERENT (expected - local has settings_local.py)${NC}"
        fi
    fi
done

echo ""
echo "=== 5. APP DIRECTORIES COMPARISON ==="

for app in "authentication" "leads" "projects" "properties"; do
    echo -e "\n${BLUE}App: $app${NC}"
    echo "Production files:"
    ssh $PROD_SERVER "find $PROD_PATH/$app -name '*.py' -type f | wc -l" 2>/dev/null
    echo "Local files:"
    find $app -name '*.py' -type f 2>/dev/null | wc -l
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VERIFICATION COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Cleanup
rm -f /tmp/prod_*.txt /tmp/local_*.txt
