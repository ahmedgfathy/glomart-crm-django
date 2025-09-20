#!/bin/bash
# Glomart CRM - Services Configuration Script
# Run this script as root to configure Gunicorn and Nginx

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_input() {
    echo -e "${BLUE}[INPUT]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root"
    exit 1
fi

APP_DIR="/var/www/glomart-crm"

print_status "🔧 Configuring Glomart CRM Services..."

# Get domain name from .env file or user input
if [ -f "$APP_DIR/.env" ]; then
    DOMAIN_NAME=$(grep "ALLOWED_HOSTS" $APP_DIR/.env | cut -d'=' -f2 | cut -d',' -f1)
    SERVER_IP=$(grep "ALLOWED_HOSTS" $APP_DIR/.env | cut -d',' -f3)
else
    print_input "Enter your domain name:"
    read -r DOMAIN_NAME
    print_input "Enter your server IP:"
    read -r SERVER_IP
fi

print_status "Configuring Gunicorn service..."
cat > /etc/systemd/system/gunicorn.service << EOF
[Unit]
Description=Gunicorn daemon for Glomart CRM
After=network.target

[Service]
User=django-user
Group=www-data
WorkingDirectory=$APP_DIR
Environment="DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production"
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 3 \\
    --worker-class sync \\
    --worker-connections 1000 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --timeout 30 \\
    --keep-alive 2 \\
    --bind unix:$APP_DIR/gunicorn.sock \\
    real_estate_crm.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

print_status "Starting and enabling Gunicorn..."
systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn

# Check Gunicorn status
if systemctl is-active --quiet gunicorn; then
    print_status "Gunicorn is running successfully"
else
    print_error "Gunicorn failed to start. Check logs with: journalctl -u gunicorn"
    exit 1
fi

print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/glomart-crm << EOF
# Rate limiting
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=api:10m rate=100r/m;

server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME $SERVER_IP;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Hide server information
    server_tokens off;

    # Static files
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        
        # Compression for static files
        location ~* \\.(css|js)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            gzip_static on;
        }
        
        location ~* \\.(jpg|jpeg|png|gif|ico|svg|webp)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Media files
    location /media/ {
        alias $APP_DIR/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        
        # Security for uploads
        location ~* \\.(php|pl|py|jsp|asp|sh|cgi)\$ {
            deny all;
        }
    }

    # Rate limiting for login
    location /auth/login/ {
        limit_req zone=login burst=5 nodelay;
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/gunicorn.sock;
    }

    # Rate limiting for API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/gunicorn.sock;
    }

    # Main application
    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Deny access to sensitive files
    location ~ /\\. {
        deny all;
    }
    
    location ~ \\.(log|conf|env)\$ {
        deny all;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # File upload size
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;
}
EOF

print_status "Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/glomart-crm /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

print_status "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    print_status "Nginx configuration is valid"
    systemctl restart nginx
else
    print_error "Nginx configuration test failed"
    exit 1
fi

print_status "Setting up log rotation..."
cat > /etc/logrotate.d/glomart-crm << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 django-user django-user
    postrotate
        systemctl reload gunicorn
    endscript
}

/var/log/nginx/access.log /var/log/nginx/error.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data adm
    postrotate
        systemctl reload nginx
    endscript
}
EOF

print_status "Setting up backup script..."
cat > /usr/local/bin/backup-crm.sh << 'EOF'
#!/bin/bash
# Glomart CRM Backup Script

BACKUP_DIR="/var/backups/glomart-crm"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/var/www/glomart-crm"

# Load environment variables
source $APP_DIR/.env

# Create backup directory
mkdir -p $BACKUP_DIR/database
mkdir -p $BACKUP_DIR/files

# Database backup
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME | gzip > $BACKUP_DIR/database/crm_db_$DATE.sql.gz

# Files backup
tar -czf $BACKUP_DIR/files/crm_files_$DATE.tar.gz -C $APP_DIR media/ logs/ --exclude='*.pyc' --exclude='__pycache__'

# Keep only last 7 days of backups
find $BACKUP_DIR/database -name "*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR/files -name "*.tar.gz" -mtime +7 -delete

echo "$(date): Backup completed - $DATE" >> /var/log/crm-backup.log
EOF

chmod +x /usr/local/bin/backup-crm.sh

print_status "Setting up health check script..."
cat > /usr/local/bin/health-check-crm.sh << EOF
#!/bin/bash
# Simple health check for Glomart CRM

SITE_URL="http://$DOMAIN_NAME"
LOG_FILE="/var/log/crm-health.log"

# Check if site is responding
if curl -s --head \$SITE_URL | head -n 1 | grep -q "200 OK"; then
    echo "\$(date): Site is UP" >> \$LOG_FILE
else
    echo "\$(date): Site is DOWN - restarting services" >> \$LOG_FILE
    systemctl restart gunicorn
    systemctl restart nginx
    
    # Send notification (you can customize this)
    echo "Glomart CRM is down. Services restarted." | mail -s "CRM Alert" admin@$DOMAIN_NAME 2>/dev/null || true
fi
EOF

chmod +x /usr/local/bin/health-check-crm.sh

print_status "Setting up cron jobs..."
cat > /tmp/crontab_root << EOF
# Backup daily at 2 AM
0 2 * * * /usr/local/bin/backup-crm.sh

# Health check every 5 minutes
*/5 * * * * /usr/local/bin/health-check-crm.sh

# Clear Django sessions weekly
0 3 * * 0 cd $APP_DIR && $APP_DIR/venv/bin/python manage.py clearsessions

# Collect static files (in case of updates) - weekly
0 4 * * 0 cd $APP_DIR && $APP_DIR/venv/bin/python manage.py collectstatic --noinput
EOF

crontab /tmp/crontab_root
rm /tmp/crontab_root

print_status "✅ Services configuration completed!"
echo
print_status "Service Status:"
systemctl status gunicorn --no-pager -l
systemctl status nginx --no-pager -l
echo
print_warning "Next steps:"
echo "1. Set up SSL certificate: sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME"
echo "2. Test the application: http://$DOMAIN_NAME"
echo "3. Monitor logs: journalctl -u gunicorn -f"
echo "4. Configure email settings in $APP_DIR/.env"
echo
print_status "Your Glomart CRM is now ready for production!"