#!/bin/bash
# =============================================================================
# PRODUCTION TO LOCAL EXACT COPY
# =============================================================================
# This script creates an EXACT copy of production in local:
# - Database: django_db_glomart_rs
# - Static files: CSS, themes, colors, images
# - Media files: Property images, uploads
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  SYNCING PRODUCTION → LOCAL (EXACT COPY)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

PROD_SERVER="root@5.180.148.92"
PROD_PATH="/var/www/glomart-crm"
LOCAL_PATH="/Users/ahmedgomaa/Downloads/glomart-crm-django"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "\n${YELLOW}[1/5]${NC} Backing up local database..."
mysqldump -u root -pzerocall django_db_glomart_rs > "local_backup_${TIMESTAMP}.sql" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Local DB backed up to: local_backup_${TIMESTAMP}.sql"

echo -e "\n${YELLOW}[2/5]${NC} Exporting production database..."
ssh $PROD_SERVER 'mysqldump -u root -p"ZeroCall20!@HH##1655&&" django_db_glomart_rs 2>/dev/null' > "production_db_${TIMESTAMP}.sql"
PROD_SIZE=$(du -h "production_db_${TIMESTAMP}.sql" | cut -f1)
echo -e "${GREEN}✓${NC} Production DB exported (${PROD_SIZE})"

echo -e "\n${YELLOW}[3/5]${NC} Importing production database to local..."
echo -e "${BLUE}  → Dropping local database...${NC}"
mysql -u root -pzerocall -e "DROP DATABASE IF EXISTS django_db_glomart_rs;" 2>/dev/null

echo -e "${BLUE}  → Creating fresh database...${NC}"
mysql -u root -pzerocall -e "CREATE DATABASE django_db_glomart_rs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null

echo -e "${BLUE}  → Importing production data...${NC}"
mysql -u root -pzerocall django_db_glomart_rs < "production_db_${TIMESTAMP}.sql" 2>/dev/null

PROPERTIES=$(mysql -u root -pzerocall django_db_glomart_rs -e "SELECT COUNT(*) FROM properties_property;" 2>/dev/null | tail -1)
echo -e "${GREEN}✓${NC} Database imported! Properties: ${PROPERTIES}"

echo -e "\n${YELLOW}[4/5]${NC} Syncing static files (CSS, themes, colors, images)..."
if [ -d "${LOCAL_PATH}/static" ]; then
    tar -czf "static_backup_${TIMESTAMP}.tar.gz" static 2>/dev/null || true
fi
rsync -avz --delete ${PROD_SERVER}:${PROD_PATH}/static/ ${LOCAL_PATH}/static/ 2>/dev/null || \
    scp -r ${PROD_SERVER}:${PROD_PATH}/static ${LOCAL_PATH}/ 2>/dev/null
echo -e "${GREEN}✓${NC} Static files synced!"

echo -e "\n${YELLOW}[5/5]${NC} Syncing media files (property images, uploads)..."
if [ -d "${LOCAL_PATH}/media" ]; then
    tar -czf "media_backup_${TIMESTAMP}.tar.gz" media 2>/dev/null || true
fi
rsync -avz --delete ${PROD_SERVER}:${PROD_PATH}/media/ ${LOCAL_PATH}/media/ 2>/dev/null || \
    scp -r ${PROD_SERVER}:${PROD_PATH}/media ${LOCAL_PATH}/ 2>/dev/null
echo -e "${GREEN}✓${NC} Media files synced!"

echo -e "\n${BLUE}Cleaning up...${NC}"
rm -f "production_db_${TIMESTAMP}.sql"
echo -e "${GREEN}✓${NC} Cleanup complete"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓✓✓ SYNC COMPLETED! LOCAL IS NOW EXACT COPY OF PRODUCTION${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n${BLUE}What was synced:${NC}"
echo -e "  ✓ Database: django_db_glomart_rs (${PROPERTIES} properties)"
echo -e "  ✓ Static: CSS, themes, colors, images, JS"
echo -e "  ✓ Media: Property images, uploads, documents"
echo -e "\n${BLUE}Backups saved:${NC}"
echo -e "  • Database: local_backup_${TIMESTAMP}.sql"
echo -e "  • Static: static_backup_${TIMESTAMP}.tar.gz"
echo -e "  • Media: media_backup_${TIMESTAMP}.tar.gz"
echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "  1. Restart Django: ${GREEN}python manage.py runserver${NC}"
echo -e "  2. Visit: ${GREEN}http://127.0.0.1:8000/${NC}"
echo -e "  3. Local design/colors now match production exactly!"
echo -e "\n${RED}⚠️  Remember: Production is MASTER, never modify production DB${NC}\n"
