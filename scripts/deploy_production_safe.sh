#!/bin/bash
# Safe Production Deployment Script
# This script ensures production database safety during deployments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/glomart-crm"
BACKUP_DIR="/var/backups/glomart-crm"
LOG_FILE="/var/log/glomart-crm/deployment.log"
VENV_PATH="$PROJECT_DIR/venv"
SERVICE_NAME="glomart-crm"

# CRITICAL: PRODUCTION DATABASE IS MASTER - NEVER TOUCH IT!
# Database credentials: root/ZeroCall20!@HH##1655&&
# This script will ONLY deploy code, never modify database

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    echo "[ERROR] $1" >> "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
    echo "[SUCCESS] $1" >> "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

# Pre-deployment checks
check_prerequisites() {
    log "Performing pre-deployment checks..."
    
    # Check if we're running as correct user
    if [[ $(whoami) != "www-data" && $(whoami) != "root" ]]; then
        error "This script should be run as www-data or root user"
    fi
    
    # Check if project directory exists
    if [[ ! -d "$PROJECT_DIR" ]]; then
        error "Project directory $PROJECT_DIR does not exist"
    fi
    
    # Check if virtual environment exists
    if [[ ! -d "$VENV_PATH" ]]; then
        error "Virtual environment not found at $VENV_PATH"
    fi
    
    # Check if backup directory exists, create if not
    mkdir -p "$BACKUP_DIR"
    
    # Check if log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    success "Pre-deployment checks passed"
}

# Backup current version
backup_current_version() {
    log "Creating backup of current version..."
    
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    
    # Create backup directory
    mkdir -p "$BACKUP_PATH"
    
    # Backup application files (excluding media and database)
    rsync -av --exclude='media/' --exclude='*.log' --exclude='__pycache__/' \
          --exclude='.git/' --exclude='venv/' \
          "$PROJECT_DIR/" "$BACKUP_PATH/"
    
    # Backup database (without affecting production)
    log "Creating database backup..."
    source "$VENV_PATH/bin/activate"
    cd "$PROJECT_DIR"
    
    # Use Django's dumpdata to safely backup
    export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
    python manage.py dumpdata --natural-foreign --natural-primary \
        --exclude=contenttypes --exclude=auth.Permission \
        > "$BACKUP_PATH/database_backup_$BACKUP_TIMESTAMP.json"
    
    success "Backup created at $BACKUP_PATH"
    echo "$BACKUP_PATH" > /tmp/last_backup_path
}

# Pull latest changes from git
update_code() {
    log "Updating code from git..."
    
    cd "$PROJECT_DIR"
    
    # Stash any local changes (shouldn't be any in production)
    git stash push -m "Auto-stash before deployment $(date)"
    
    # Fetch latest changes
    git fetch origin main
    
    # Reset to latest main (hard reset for clean deployment)
    git reset --hard origin/main
    
    success "Code updated successfully"
}

# Install/update dependencies
update_dependencies() {
    log "Installing/updating Python dependencies..."
    
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    
    # Update pip first
    pip install --upgrade pip
    
    # Install production requirements
    pip install -r requirements-production.txt
    
    success "Dependencies updated successfully"
}

# CRITICAL: NO DATABASE MODIFICATIONS IN PRODUCTION!
# The production database contains master data and must NEVER be touched
check_migrations_only() {
    log "Checking migrations (READ-ONLY, no modifications)..."
    
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
    
    # Only check migration status, never apply
    log "Current migration status:"
    python manage.py showmigrations
    
    # If there are unapplied migrations, warn but DO NOT apply
    if python manage.py showmigrations --plan | grep -q "\[ \]"; then
        warning "⚠️  UNAPPLIED MIGRATIONS DETECTED!"
        warning "⚠️  Production database is MASTER data - migrations NOT applied automatically"
        warning "⚠️  Please review migrations carefully before manual application"
        
        # Log which migrations are pending
        python manage.py showmigrations --plan | grep "\[ \]" >> "$LOG_FILE"
    else
        log "All migrations are up to date"
    fi
}

# Collect static files
collect_static() {
    log "Collecting static files..."
    
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
    
    # Clear old static files first
    python manage.py collectstatic --clear --noinput
    
    success "Static files collected successfully"
}

# Set proper permissions
set_permissions() {
    log "Setting proper file permissions..."
    
    # Set ownership to www-data
    chown -R www-data:www-data "$PROJECT_DIR"
    
    # Set directory permissions
    find "$PROJECT_DIR" -type d -exec chmod 755 {} \;
    
    # Set file permissions
    find "$PROJECT_DIR" -type f -exec chmod 644 {} \;
    
    # Make manage.py executable
    chmod +x "$PROJECT_DIR/manage.py"
    
    # Secure sensitive files
    chmod 600 "$PROJECT_DIR/.env.production" 2>/dev/null || true
    
    success "Permissions set successfully"
}

# Restart services
restart_services() {
    log "Restarting services..."
    
    # Reload systemd daemon
    systemctl daemon-reload
    
    # Restart Gunicorn service
    systemctl restart "$SERVICE_NAME"
    
    # Reload Nginx (graceful reload)
    systemctl reload nginx
    
    success "Services restarted successfully"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait for service to start
    sleep 5
    
    # Check if service is running
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        error "Service $SERVICE_NAME is not running after restart"
    fi
    
    # Check if application responds
    if curl -f -s http://127.0.0.1:8000/admin/ > /dev/null; then
        success "Application health check passed"
    else
        warning "Application might not be responding correctly, check logs"
    fi
}

# Cleanup old backups (keep last 10)
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    cd "$BACKUP_DIR"
    ls -t backup_* | tail -n +11 | xargs rm -rf 2>/dev/null || true
    
    success "Old backups cleaned up"
}

# Rollback function (in case something goes wrong)
rollback() {
    error "Deployment failed, initiating rollback..."
    
    if [[ -f /tmp/last_backup_path ]]; then
        LAST_BACKUP=$(cat /tmp/last_backup_path)
        if [[ -d "$LAST_BACKUP" ]]; then
            log "Rolling back to $LAST_BACKUP..."
            
            # Stop service
            systemctl stop "$SERVICE_NAME" || true
            
            # Restore files
            rsync -av "$LAST_BACKUP/" "$PROJECT_DIR/"
            
            # Set permissions
            set_permissions
            
            # Restart service
            systemctl start "$SERVICE_NAME"
            systemctl reload nginx
            
            warning "Rollback completed. Please check the application."
        fi
    fi
}

# Main deployment function
main() {
    log "Starting production deployment..."
    
    # Set up error handling
    trap rollback ERR
    
    # Run deployment steps (NO DATABASE MODIFICATIONS!)
    check_prerequisites
    backup_current_version
    update_code
    update_dependencies
    check_migrations_only  # Changed from run_migrations - READ ONLY!
    collect_static
    set_permissions
    restart_services
    health_check
    cleanup_old_backups
    
    success "🚀 Deployment completed successfully!"
    log "Deployment finished at $(date)"
}

# Run main function
main "$@"