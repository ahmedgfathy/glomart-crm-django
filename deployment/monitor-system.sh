#!/bin/bash
# Glomart CRM - System Monitor Script
# Checks system health and sends alerts if needed

LOG_FILE="/var/log/crm-monitor.log"
APP_DIR="/var/www/glomart-crm"
ALERT_EMAIL="admin@yourdomain.com"  # Change this to your email

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" $ALERT_EMAIL 2>/dev/null || true
    log_message "ALERT: $subject - $message"
}

check_service() {
    local service_name="$1"
    if systemctl is-active --quiet $service_name; then
        echo -e "${GREEN}✓${NC} $service_name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name is not running"
        log_message "ERROR: $service_name is not running"
        send_alert "CRM Service Down" "$service_name service is not running on $(hostname)"
        return 1
    fi
}

check_disk_space() {
    local threshold=85
    local usage=$(df /var | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ $usage -gt $threshold ]; then
        echo -e "${RED}✗${NC} Disk usage is ${usage}% (threshold: ${threshold}%)"
        log_message "WARNING: High disk usage - ${usage}%"
        send_alert "CRM Disk Space Warning" "Disk usage is at ${usage}% on $(hostname)"
        return 1
    else
        echo -e "${GREEN}✓${NC} Disk usage is ${usage}%"
        return 0
    fi
}

check_memory() {
    local threshold=85
    local usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    
    if [ $usage -gt $threshold ]; then
        echo -e "${RED}✗${NC} Memory usage is ${usage}% (threshold: ${threshold}%)"
        log_message "WARNING: High memory usage - ${usage}%"
        send_alert "CRM Memory Warning" "Memory usage is at ${usage}% on $(hostname)"
        return 1
    else
        echo -e "${GREEN}✓${NC} Memory usage is ${usage}%"
        return 0
    fi
}

check_website() {
    local url="http://localhost"
    local response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} Website is responding (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗${NC} Website is not responding (HTTP $response)"
        log_message "ERROR: Website not responding - HTTP $response"
        send_alert "CRM Website Down" "Website is not responding with HTTP $response on $(hostname)"
        return 1
    fi
}

check_database() {
    cd $APP_DIR
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
    
    if python manage.py shell -c "from django.db import connection; connection.cursor().execute('SELECT 1')" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Database connection is working"
        return 0
    else
        echo -e "${RED}✗${NC} Database connection failed"
        log_message "ERROR: Database connection failed"
        send_alert "CRM Database Error" "Database connection failed on $(hostname)"
        return 1
    fi
}

check_log_errors() {
    local error_count=$(tail -100 $APP_DIR/logs/django.log 2>/dev/null | grep -i error | wc -l)
    
    if [ $error_count -gt 10 ]; then
        echo -e "${YELLOW}⚠${NC} Found $error_count errors in recent logs"
        log_message "WARNING: High error count in logs - $error_count"
        send_alert "CRM High Error Count" "Found $error_count errors in recent Django logs on $(hostname)"
        return 1
    else
        echo -e "${GREEN}✓${NC} Log errors are within normal range ($error_count)"
        return 0
    fi
}

# Main monitoring function
main() {
    echo "🔍 Glomart CRM System Health Check - $(date)"
    echo "================================================"
    
    local issues=0
    
    echo "📊 System Resources:"
    check_disk_space || ((issues++))
    check_memory || ((issues++))
    
    echo
    echo "🔧 Services:"
    check_service "gunicorn" || ((issues++))
    check_service "nginx" || ((issues++))
    check_service "mariadb" || ((issues++))
    
    echo
    echo "🌐 Application:"
    check_website || ((issues++))
    check_database || ((issues++))
    check_log_errors || ((issues++))
    
    echo
    echo "================================================"
    
    if [ $issues -eq 0 ]; then
        echo -e "${GREEN}✅ All checks passed - System is healthy${NC}"
        log_message "INFO: All health checks passed"
    else
        echo -e "${RED}❌ Found $issues issues - Check logs for details${NC}"
        log_message "WARNING: Health check found $issues issues"
    fi
    
    echo
}

# Run the main function
main

# Cleanup old log entries (keep last 1000 lines)
if [ -f $LOG_FILE ]; then
    tail -1000 $LOG_FILE > $LOG_FILE.tmp && mv $LOG_FILE.tmp $LOG_FILE
fi