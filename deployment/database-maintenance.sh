#!/bin/bash
# Glomart CRM - Database Maintenance Script
# Performs routine database maintenance tasks

APP_DIR="/var/www/glomart-crm"
BACKUP_DIR="/var/backups/glomart-crm"
LOG_FILE="/var/log/crm-maintenance.log"

# Source environment variables
source $APP_DIR/.env

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
    log_message "INFO: $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log_message "WARNING: $1"
}

print_task() {
    echo -e "${BLUE}[TASK]${NC} $1"
    log_message "TASK: $1"
}

# Database optimization
optimize_database() {
    print_task "Optimizing database tables..."
    
    # Get list of tables
    tables=$(mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "SHOW TABLES;" | grep -v Tables_in)
    
    for table in $tables; do
        print_status "Optimizing table: $table"
        mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "OPTIMIZE TABLE $table;" >> $LOG_FILE 2>&1
    done
    
    print_status "Database optimization completed"
}

# Clean up Django sessions
cleanup_sessions() {
    print_task "Cleaning up expired Django sessions..."
    
    cd $APP_DIR
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
    
    python manage.py clearsessions
    print_status "Session cleanup completed"
}

# Clean up old log files
cleanup_logs() {
    print_task "Cleaning up old log files..."
    
    # Keep last 30 days of logs
    find $APP_DIR/logs -name "*.log.*" -mtime +30 -delete
    find /var/log -name "*crm*" -mtime +30 -delete
    
    # Compress old logs
    find $APP_DIR/logs -name "*.log" -size +10M -exec gzip {} \;
    
    print_status "Log cleanup completed"
}

# Analyze database performance
analyze_performance() {
    print_task "Analyzing database performance..."
    
    # Check for slow queries
    mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "
        SELECT 
            ROUND(SUM(total_latency)/1000000) as exec_time_ms,
            exec_count,
            query_sample_text 
        FROM performance_schema.events_statements_summary_by_digest 
        WHERE digest_text IS NOT NULL 
        ORDER BY SUM(total_latency) DESC 
        LIMIT 10;
    " 2>/dev/null || print_warning "Performance schema not available"
    
    # Check table sizes
    mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "
        SELECT 
            table_name AS 'Table',
            ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
        FROM information_schema.tables 
        WHERE table_schema = '$DB_NAME'
        ORDER BY (data_length + index_length) DESC;
    " >> $LOG_FILE
    
    print_status "Performance analysis completed"
}

# Backup with compression and verification
create_backup() {
    print_task "Creating verified database backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/database/crm_db_$timestamp.sql.gz"
    
    # Create backup
    mysqldump -u $DB_USER -p$DB_PASSWORD \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        $DB_NAME | gzip > $backup_file
    
    # Verify backup
    if gunzip -t $backup_file; then
        print_status "Backup created and verified: $backup_file"
    else
        print_warning "Backup verification failed: $backup_file"
        return 1
    fi
    
    # Clean old backups (keep 7 days)
    find $BACKUP_DIR/database -name "*.sql.gz" -mtime +7 -delete
    
    print_status "Backup cleanup completed"
}

# Check database integrity
check_integrity() {
    print_task "Checking database integrity..."
    
    # Check all tables
    tables=$(mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "SHOW TABLES;" | grep -v Tables_in)
    
    for table in $tables; do
        result=$(mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "CHECK TABLE $table;" | grep -v Table | awk '{print $4}')
        if [ "$result" = "OK" ]; then
            print_status "Table $table: OK"
        else
            print_warning "Table $table: $result"
        fi
    done
    
    print_status "Integrity check completed"
}

# Update database statistics
update_statistics() {
    print_task "Updating database statistics..."
    
    tables=$(mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "SHOW TABLES;" | grep -v Tables_in)
    
    for table in $tables; do
        mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "ANALYZE TABLE $table;" >> $LOG_FILE 2>&1
    done
    
    print_status "Statistics update completed"
}

# Main maintenance function
main() {
    print_status "🛠️ Starting Glomart CRM Database Maintenance - $(date)"
    print_status "================================================"
    
    # Check if database is accessible
    if ! mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "SELECT 1;" > /dev/null 2>&1; then
        print_warning "Cannot connect to database. Exiting."
        exit 1
    fi
    
    # Run maintenance tasks
    create_backup
    cleanup_sessions
    cleanup_logs
    check_integrity
    update_statistics
    optimize_database
    analyze_performance
    
    print_status "================================================"
    print_status "✅ Database maintenance completed successfully"
    
    # Generate summary report
    echo "📊 Maintenance Summary:" >> $LOG_FILE
    echo "- Backup created: $(ls -1 $BACKUP_DIR/database/*.gz | tail -1)" >> $LOG_FILE
    echo "- Database size: $(mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size in MB' FROM information_schema.tables WHERE table_schema='$DB_NAME';" | tail -1) MB" >> $LOG_FILE
    echo "- Total tables: $(mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME';" | tail -1)" >> $LOG_FILE
    echo "================================================" >> $LOG_FILE
}

# Run main function
main