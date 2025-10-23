#!/bin/bash
# Script to safely copy production data TO local development
# PRODUCTION DATABASE IS MASTER - this only copies FROM production TO local

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Database configurations
PROD_DB_HOST="5.180.148.92"  # Your production server IP
PROD_DB_NAME="django_db_glomart_rs"
PROD_DB_USER="root"
PROD_DB_PASS="ZeroCall20!@HH##1655&&"

LOCAL_DB_HOST="localhost"
LOCAL_DB_NAME="django_db_glomart_rs"
LOCAL_DB_USER="root"
LOCAL_DB_PASS="zerocall"

# Check if we're in the right directory
if [[ ! -f "manage.py" ]]; then
    error "This script must be run from the Django project root directory"
fi

# Check if local virtual environment exists
if [[ ! -d "venv" ]]; then
    error "Virtual environment not found. Please run from project directory with venv/"
fi

# Activate virtual environment
source venv/bin/activate

log "🔄 Starting production data sync TO local development..."
warning "⚠️  This will REPLACE local development data with production master data"
warning "⚠️  Production database will NOT be touched - only READ from"

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Operation cancelled"
    exit 0
fi

# Test production database connection (READ-ONLY)
log "Testing production database connection (READ-ONLY)..."
if ! mysql -h"$PROD_DB_HOST" -u"$PROD_DB_USER" -p"$PROD_DB_PASS" "$PROD_DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
    error "Cannot connect to production database. Please check connection details."
fi
success "Production database connection successful"

# Test local database connection
log "Testing local database connection..."
if ! mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
    error "Cannot connect to local database. Please ensure local MariaDB is running."
fi
success "Local database connection successful"

# Create backup of current local data (just in case)
log "Creating backup of current local data..."
BACKUP_FILE="local_backup_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" > "$BACKUP_FILE"
success "Local data backed up to $BACKUP_FILE"

# Export production data (READ-ONLY operation)
log "Exporting production data (READ-ONLY)..."
PROD_EXPORT_FILE="production_data_$(date +%Y%m%d_%H%M%S).sql"

# Export production database structure and data
mysqldump -h"$PROD_DB_HOST" -u"$PROD_DB_USER" -p"$PROD_DB_PASS" \
    --single-transaction \
    --routines \
    --triggers \
    --no-create-db \
    "$PROD_DB_NAME" > "$PROD_EXPORT_FILE"

success "Production data exported to $PROD_EXPORT_FILE"

# Import into local database
log "Importing production data into local database..."

# Drop and recreate local database to ensure clean import
mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" -e "DROP DATABASE IF EXISTS $LOCAL_DB_NAME;"
mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" -e "CREATE DATABASE $LOCAL_DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Import the production data
mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" < "$PROD_EXPORT_FILE"

success "Production data imported into local database"

# Run Django migrations in case there are local schema changes
log "Running Django migrations on local database..."
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local
python manage.py migrate --noinput

# Create local superuser if needed (since we now have production data)
log "Checking for admin user in local database..."
python -c "
import django
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    print('Creating local admin user...')
    User.objects.create_superuser('admin', 'admin@localhost.com', 'admin123')
    print('Local admin user created')
else:
    print('Admin user already exists')
"

# Update file permissions and cleanup
log "Cleaning up temporary files..."
rm -f "$PROD_EXPORT_FILE"  # Remove production export file for security
success "Cleanup completed"

# =============================================================================
# Sync static files (CSS, themes, images)
# =============================================================================
log "🎨 Syncing static files from production..."
PROD_SERVER="root@5.180.148.92"
PROD_PATH="/var/www/glomart-crm"
LOCAL_PATH="/Users/ahmedgomaa/Downloads/glomart-crm-django"

# Backup local static files
if [ -d "${LOCAL_PATH}/static" ]; then
    log "Backing up local static files..."
    tar -czf "local_static_backup_$(date +%Y%m%d_%H%M%S).tar.gz" -C "${LOCAL_PATH}" static 2>/dev/null || true
    success "Local static files backed up"
fi

# Sync production static files
log "Downloading production static files (CSS, JS, images, themes)..."
rsync -avz --delete "$PROD_SERVER:$PROD_PATH/static/" "${LOCAL_PATH}/static/" 2>/dev/null || {
    warning "rsync failed, trying scp..."
    rm -rf "${LOCAL_PATH}/static"
    scp -r "$PROD_SERVER:$PROD_PATH/static" "${LOCAL_PATH}/" 2>/dev/null
}
success "Static files synced from production!"

# =============================================================================
# Sync media files (user uploads, property images)
# =============================================================================
log "📷 Syncing media files from production..."

# Backup local media files
if [ -d "${LOCAL_PATH}/media" ]; then
    log "Backing up local media files..."
    tar -czf "local_media_backup_$(date +%Y%m%d_%H%M%S).tar.gz" -C "${LOCAL_PATH}" media 2>/dev/null || true
    success "Local media files backed up"
fi

# Sync production media files
log "Downloading production media files (this may take a while)..."
rsync -avz --delete "$PROD_SERVER:$PROD_PATH/media/" "${LOCAL_PATH}/media/" 2>/dev/null || {
    warning "rsync failed, trying scp..."
    rm -rf "${LOCAL_PATH}/media"
    scp -r "$PROD_SERVER:$PROD_PATH/media" "${LOCAL_PATH}/" 2>/dev/null
}
success "Media files synced from production!"

success "🎉 Production data successfully copied to local development!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "📊 SYNC SUMMARY - Local is now an EXACT copy of production!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ Database: Production data copied to django_db_glomart_rs"
log "✅ Static Files: CSS, themes, colors, images synced"
log "✅ Media Files: Property images and uploads synced"
log "📊 You now have the master production data in your local environment"
log "🔐 Local admin login: admin / admin123"
log "💾 Previous local data backed up to: $BACKUP_FILE"
log "🚨 Remember: Production database was NOT modified - only copied FROM"

log "\n🚀 NEXT STEPS:"
log "   1. Restart Django server: python manage.py runserver"
log "   2. Visit: http://127.0.0.1:8000/"
log "   3. Local design/colors should now match production exactly!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

warning "⚠️  IMPORTANT REMINDERS:"
warning "   1. Production database (master) was NOT touched"
warning "   2. This local data should be used for development/testing only"
warning "   3. Never push local database changes back to production"
warning "   4. Always sync FROM production when you need fresh data"