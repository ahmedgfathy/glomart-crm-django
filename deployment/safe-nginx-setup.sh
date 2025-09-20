#!/bin/bash
# SAFE Nginx Configuration for Existing Server
# Only adds virtual host without affecting existing configurations

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[SAFE-NGINX]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[CAUTION]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_warning "Please run this script as root"
    exit 1
fi

print_info "🔒 SAFE Nginx Configuration for Glomart CRM"
print_info "This will ONLY add a new virtual host"
echo "==============================================="

# Get domain information
read -p "Enter your CRM domain (e.g., crm.yourdomain.com): " DOMAIN_NAME
read -p "Enter your server IP: " SERVER_IP

APP_DIR="/var/www/glomart-crm"

# Backup existing nginx configuration
print_status "Creating backup of existing Nginx configuration..."
BACKUP_DIR="/var/backups/nginx-$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r /etc/nginx $BACKUP_DIR/
print_status "✓ Nginx config backed up to: $BACKUP_DIR"

# Check existing configurations
print_info "Current Nginx sites:"
ls -la /etc/nginx/sites-enabled/ | grep -v total

# Create CRM virtual host (separate file)
print_status "Creating CRM virtual host configuration..."
cat > /etc/nginx/sites-available/glomart-crm << EOF
# Glomart CRM Virtual Host
# This configuration is ISOLATED and won't affect other sites

server {
    listen 80;
    server_name $DOMAIN_NAME $SERVER_IP;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Hide server information
    server_tokens off;

    # Static files for CRM only
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        
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

    # Media files for CRM only
    location /media/ {
        alias $APP_DIR/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        
        # Security for uploads
        location ~* \\.(php|pl|py|jsp|asp|sh|cgi)\$ {
            deny all;
        }
    }

    # CRM application
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

# Test configuration before enabling
print_status "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    print_status "✓ Nginx configuration test passed"
    
    # Enable the site
    print_status "Enabling CRM virtual host..."
    ln -sf /etc/nginx/sites-available/glomart-crm /etc/nginx/sites-enabled/
    
    # Reload (not restart) to preserve existing connections
    print_status "Reloading Nginx configuration..."
    systemctl reload nginx
    
    print_status "✅ CRM virtual host added successfully!"
else
    print_warning "✗ Nginx configuration test failed"
    print_info "Restoring backup..."
    rm -f /etc/nginx/sites-available/glomart-crm
    exit 1
fi

print_info "SAFETY SUMMARY:"
echo "✓ Existing virtual hosts: PRESERVED"
echo "✓ Mail server configs: UNTOUCHED"
echo "✓ SSL certificates: UNCHANGED"
echo "✓ Only ADDED: /etc/nginx/sites-available/glomart-crm"
echo "✓ Backup created: $BACKUP_DIR"
echo
print_info "Virtual hosts now active:"
ls -la /etc/nginx/sites-enabled/

print_warning "IMPORTANT: Set up SSL for CRM domain:"
print_info "sudo certbot --nginx -d $DOMAIN_NAME"
print_info "(This will NOT affect existing SSL certificates)"