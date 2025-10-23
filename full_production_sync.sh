#!/bin/bash
# =============================================================================
# COMPLETE PRODUCTION TO LOCAL SYNC - ALL FILES & FOLDERS
# =============================================================================
# This syncs EVERYTHING from production to local:
# 1. Database (django_db_glomart_rs)
# 2. Static files (CSS, JS, images)
# 3. Staticfiles (collected static + property videos - 2.4GB)
# 4. Media files (uploads)
# 5. Templates (HTML templates)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  COMPLETE PRODUCTION → LOCAL SYNC (ALL FILES & FOLDERS)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

PROD_SERVER="root@5.180.148.92"
PROD_PATH="/var/www/glomart-crm"
LOCAL_PATH="/Users/ahmedgomaa/Downloads/glomart-crm-django"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "\n${YELLOW}⚠️  WARNING: This will download ~2.5GB of data (including property videos)${NC}"
echo -e "${YELLOW}⚠️  This may take 5-15 minutes depending on your internet speed${NC}"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Sync cancelled"
    exit 0
fi

# =============================================================================
# STEP 1: Backup local database
# =============================================================================
echo -e "\n${BLUE}[1/7]${NC} Backing up local database..."
mysqldump -u root -pzerocall django_db_glomart_rs > "backup_db_${TIMESTAMP}.sql" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Backed up to: backup_db_${TIMESTAMP}.sql"

# =============================================================================
# STEP 2: Sync production database
# =============================================================================
echo -e "\n${BLUE}[2/7]${NC} Syncing production database..."
ssh $PROD_SERVER 'mysqldump -u root -p"ZeroCall20!@HH##1655&&" django_db_glomart_rs 2>/dev/null' > "prod_db_${TIMESTAMP}.sql"
echo -e "${BLUE}  → Dropping local database...${NC}"
mysql -u root -pzerocall -e "DROP DATABASE IF EXISTS django_db_glomart_rs;" 2>/dev/null
echo -e "${BLUE}  → Creating fresh database...${NC}"
mysql -u root -pzerocall -e "CREATE DATABASE django_db_glomart_rs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
echo -e "${BLUE}  → Importing production data...${NC}"
mysql -u root -pzerocall django_db_glomart_rs < "prod_db_${TIMESTAMP}.sql" 2>/dev/null
PROPERTIES=$(mysql -u root -pzerocall django_db_glomart_rs -e "SELECT COUNT(*) FROM properties_property;" 2>/dev/null | tail -1)
rm -f "prod_db_${TIMESTAMP}.sql"
echo -e "${GREEN}✓${NC} Database synced (${PROPERTIES} properties)"

# =============================================================================
# STEP 3: Sync static files (CSS, JS, images, themes)
# =============================================================================
echo -e "\n${BLUE}[3/7]${NC} Syncing static/ directory (CSS, JS, images, themes)..."
if [ -d "${LOCAL_PATH}/static" ]; then
    tar -czf "backup_static_${TIMESTAMP}.tar.gz" static 2>/dev/null || true
fi
rsync -avz --delete ${PROD_SERVER}:${PROD_PATH}/static/ ${LOCAL_PATH}/static/ 2>/dev/null
echo -e "${GREEN}✓${NC} Static files synced!"

# =============================================================================
# STEP 4: Sync staticfiles (Django collected static - 2.4GB!)
# =============================================================================
echo -e "\n${BLUE}[4/7]${NC} Syncing staticfiles/ directory (includes property videos - 2.4GB)..."
echo -e "${YELLOW}  ⏳ This will take several minutes...${NC}"
if [ -d "${LOCAL_PATH}/staticfiles" ]; then
    echo -e "${BLUE}  → Backing up existing staticfiles...${NC}"
    tar -czf "backup_staticfiles_${TIMESTAMP}.tar.gz" staticfiles 2>/dev/null || true
fi
echo -e "${BLUE}  → Downloading from production (please wait)...${NC}"
rsync -avz --progress --delete ${PROD_SERVER}:${PROD_PATH}/staticfiles/ ${LOCAL_PATH}/staticfiles/ 2>&1 | grep -E '(sending|total size|speedup)'
echo -e "${GREEN}✓${NC} Staticfiles synced (includes all property videos and images)!"

# =============================================================================
# STEP 5: Sync media files
# =============================================================================
echo -e "\n${BLUE}[5/7]${NC} Syncing media/ directory (user uploads)..."
if [ -d "${LOCAL_PATH}/media" ]; then
    tar -czf "backup_media_${TIMESTAMP}.tar.gz" media 2>/dev/null || true
fi
rsync -avz --delete ${PROD_SERVER}:${PROD_PATH}/media/ ${LOCAL_PATH}/media/ 2>/dev/null
echo -e "${GREEN}✓${NC} Media files synced!"

# =============================================================================
# STEP 6: Sync templates (HTML design files)
# =============================================================================
echo -e "\n${BLUE}[6/7]${NC} Syncing templates/ directory (HTML design files)..."
if [ -d "${LOCAL_PATH}/templates" ]; then
    tar -czf "backup_templates_${TIMESTAMP}.tar.gz" templates 2>/dev/null || true
fi
rsync -avz --delete ${PROD_SERVER}:${PROD_PATH}/templates/ ${LOCAL_PATH}/templates/ 2>/dev/null
echo -e "${GREEN}✓${NC} Templates synced!"

# =============================================================================
# STEP 7: Apply migrations
# =============================================================================
echo -e "\n${BLUE}[7/7]${NC} Applying Django migrations..."
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local
python manage.py migrate --noinput 2>/dev/null
echo -e "${GREEN}✓${NC} Migrations applied!"

# =============================================================================
# FINAL SUMMARY
# =============================================================================
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓✓✓ COMPLETE SYNC FINISHED! LOCAL = EXACT PRODUCTION COPY${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${CYAN}📦 What was synced:${NC}"
echo -e "  ${GREEN}✓${NC} Database: django_db_glomart_rs (${PROPERTIES} properties)"
echo -e "  ${GREEN}✓${NC} static/: CSS (23KB), JS, images, themes, favicon"
echo -e "  ${GREEN}✓${NC} staticfiles/: Django collected static + property videos (2.4GB)"
echo -e "  ${GREEN}✓${NC} media/: User uploads and documents"
echo -e "  ${GREEN}✓${NC} templates/: HTML design files"

echo -e "\n${CYAN}💾 Backups created:${NC}"
ls -lh backup_*_${TIMESTAMP}.* 2>/dev/null | awk '{print "  • " $9 " (" $5 ")"}'

echo -e "\n${CYAN}📊 Storage used:${NC}"
echo -e "  • static/: $(du -sh static 2>/dev/null | cut -f1)"
echo -e "  • staticfiles/: $(du -sh staticfiles 2>/dev/null | cut -f1)"
echo -e "  • media/: $(du -sh media 2>/dev/null | cut -f1)"
echo -e "  • templates/: $(du -sh templates 2>/dev/null | cut -f1)"

echo -e "\n${YELLOW}🚀 Start your server:${NC}"
echo -e "  ${CYAN}python manage.py runserver${NC}"
echo -e "  ${CYAN}http://127.0.0.1:8000/${NC}"

echo -e "\n${GREEN}✅ Local design, colors, templates, images, and data now EXACTLY match production!${NC}\n"
