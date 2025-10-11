#!/bin/bash
# Import production data to local database
# Run this on your LOCAL machine after downloading the export file

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if export file is provided
if [ $# -eq 0 ]; then
    error "Please provide the production export file"
    echo "Usage: ./import_production_data.sh <export_file.sql>"
    exit 1
fi

EXPORT_FILE="$1"

# Check if export file exists
if [ ! -f "$EXPORT_FILE" ]; then
    error "Export file '$EXPORT_FILE' not found!"
fi

log "🔄 Starting production data import to local database..."
log "📄 Import file: $EXPORT_FILE"
log "📊 File size: $(du -h "$EXPORT_FILE" | cut -f1)"

# Local database configuration
LOCAL_DB_HOST="localhost"
LOCAL_DB_NAME="glomart_crm_local"
LOCAL_DB_USER="root"
LOCAL_DB_PASS="zerocall"

# Test local database connection
log "🔌 Testing local database connection..."
if ! mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" -e "SELECT 1;" >/dev/null 2>&1; then
    error "Cannot connect to local database! Please check MariaDB is running and credentials are correct."
fi
success "Local database connection successful"

# Backup current local database
log "💾 Creating backup of current local database..."
BACKUP_FILE="local_backup_before_production_import_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" > "$BACKUP_FILE"
success "Local database backed up to: $BACKUP_FILE"

warning "This will REPLACE your local database with ALL production data"
warning "Your current local data has been backed up to: $BACKUP_FILE"
read -p "Continue with import? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Import cancelled"
    exit 0
fi

# Drop and recreate local database
log "🗑️  Dropping and recreating local database..."
mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" -e "DROP DATABASE IF EXISTS $LOCAL_DB_NAME;"
mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" -e "CREATE DATABASE $LOCAL_DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Import production data
log "📥 Importing production data into local database..."
log "This may take a few minutes depending on data size..."

# Show progress during import
pv "$EXPORT_FILE" | mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" 2>/dev/null || \
mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" < "$EXPORT_FILE"

success "Production data imported successfully!"

# Get data counts
log "📊 Checking imported data counts..."
echo "Properties: $(mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" -e "SELECT COUNT(*) FROM properties_property;" -s -N)"
echo "Leads: $(mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" -e "SELECT COUNT(*) FROM leads_lead;" -s -N)"
echo "Projects: $(mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" -e "SELECT COUNT(*) FROM projects_project;" -s -N)"
echo "Users: $(mysql -h"$LOCAL_DB_HOST" -u"$LOCAL_DB_USER" -p"$LOCAL_DB_PASS" "$LOCAL_DB_NAME" -e "SELECT COUNT(*) FROM auth_user;" -s -N)"

# Run Django migrations in case of schema differences
if [ -f "manage.py" ] && [ -d "venv" ]; then
    log "🔧 Running Django migrations on imported data..."
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local
    python manage.py migrate --noinput
    success "Migrations applied successfully"
    
    # Create local admin user if needed
    log "👤 Ensuring local admin user exists..."
    python -c "
import django
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost.com', 'admin123')
    print('✅ Local admin user created: admin / admin123')
else:
    print('✅ Admin user already exists')
"
fi

success "🎉 Production data successfully imported to local database!"
log "🔐 You can now login with existing production users or admin/admin123"
log "🗄️ You now have ALL production data in your local environment"
warning "Remember: This is a COPY of production data - changes here won't affect production"

# Cleanup
log "🧹 Cleaning up..."
rm -f "$EXPORT_FILE"
success "Import completed successfully!"