# 🚀 Production Deployment Guide for Glomart CRM

## Overview
This guide will help you deploy your Django CRM system to a production server with proper security, performance, and reliability configurations.

## 📋 Prerequisites
- Server with Ubuntu 20.04+ or CentOS 8+
- Root access to the server
- Domain name (optional but recommended)
- Basic knowledge of Linux commands

## 🏗️ Architecture Overview
```
Internet → Nginx (Reverse Proxy) → Gunicorn (WSGI Server) → Django App
                ↓
            Static Files
                ↓
            MariaDB Database
```

## 📝 Step-by-Step Deployment

### Phase 1: Server Preparation

#### 1.1 Initial Server Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y software-properties-common curl wget git unzip

# Create a non-root user for security
sudo adduser django-user
sudo usermod -aG sudo django-user

# Switch to the new user
sudo su - django-user
```

#### 1.2 Install Python and Dependencies
```bash
# Install Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies
sudo apt install -y build-essential libssl-dev libffi-dev python3.11-dev
sudo apt install -y libjpeg-dev zlib1g-dev libpng-dev

# Create Python symlink for convenience
sudo ln -sf /usr/bin/python3.11 /usr/bin/python3
```

#### 1.3 Install and Configure MariaDB
```bash
# Install MariaDB
sudo apt install -y mariadb-server mariadb-client

# Secure MariaDB installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
-- In MariaDB shell:
CREATE DATABASE glomart_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'crm_user'@'localhost' IDENTIFIED BY 'your_secure_password_here';
GRANT ALL PRIVILEGES ON glomart_crm.* TO 'crm_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 1.4 Install and Configure Nginx
```bash
# Install Nginx
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Phase 2: Application Deployment

#### 2.1 Clone and Setup Application
```bash
# Create application directory
sudo mkdir -p /var/www/glomart-crm
sudo chown django-user:django-user /var/www/glomart-crm

# Clone your repository
cd /var/www/glomart-crm
git clone https://github.com/your-username/glomart-crm-django.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install production-specific packages
pip install gunicorn
pip install python-decouple
```

#### 2.2 Environment Configuration
```bash
# Create environment file
touch .env
```

```env
# .env file content:
DEBUG=False
SECRET_KEY=your_very_secure_secret_key_here_change_this
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# Database Configuration
DB_NAME=glomart_crm
DB_USER=crm_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=3306

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY

# Static and Media Files
STATIC_ROOT=/var/www/glomart-crm/staticfiles
MEDIA_ROOT=/var/www/glomart-crm/media

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

#### 2.3 Django Configuration
```bash
# Create production settings file
cp real_estate_crm/settings.py real_estate_crm/settings_production.py
```

Edit `real_estate_crm/settings_production.py`:
```python
import os
from decouple import config

# Import base settings
from .settings import *

# Production overrides
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = config('STATIC_ROOT')
MEDIA_URL = '/media/'
MEDIA_ROOT = config('MEDIA_ROOT')

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='DENY')

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/www/glomart-crm/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

#### 2.4 Application Setup
```bash
# Create logs directory
mkdir -p /var/www/glomart-crm/logs

# Set Django settings module
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create initial data (if needed)
python manage.py loaddata initial_data.json
```

### Phase 3: Web Server Configuration

#### 3.1 Gunicorn Configuration
```bash
# Create Gunicorn configuration
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=Gunicorn daemon for Glomart CRM
After=network.target

[Service]
User=django-user
Group=www-data
WorkingDirectory=/var/www/glomart-crm
Environment="DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production"
ExecStart=/var/www/glomart-crm/venv/bin/gunicorn --workers 3 --bind unix:/var/www/glomart-crm/gunicorn.sock real_estate_crm.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Start and enable Gunicorn
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

#### 3.2 Nginx Configuration
```bash
# Create Nginx site configuration
sudo nano /etc/nginx/sites-available/glomart-crm
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com your-server-ip;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Static files
    location /static/ {
        alias /var/www/glomart-crm/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Media files
    location /media/ {
        alias /var/www/glomart-crm/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Main application
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/glomart-crm/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/css text/javascript application/javascript application/json;

    # File upload size
    client_max_body_size 50M;
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/glomart-crm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Phase 4: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### Phase 5: Monitoring and Maintenance

#### 5.1 Database Backup Script
```bash
# Create backup script
sudo nano /usr/local/bin/backup-crm.sh
```

```bash
#!/bin/bash
# Glomart CRM Backup Script

BACKUP_DIR="/var/backups/glomart-crm"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="glomart_crm"
DB_USER="crm_user"
APP_DIR="/var/www/glomart-crm"

# Create backup directory
mkdir -p $BACKUP_DIR/database
mkdir -p $BACKUP_DIR/files

# Database backup
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME | gzip > $BACKUP_DIR/database/crm_db_$DATE.sql.gz

# Files backup
tar -czf $BACKUP_DIR/files/crm_files_$DATE.tar.gz -C $APP_DIR media/ logs/

# Keep only last 7 days of backups
find $BACKUP_DIR/database -name "*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR/files -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-crm.sh

# Add to crontab (daily backup at 2 AM)
sudo crontab -e
# Add line: 0 2 * * * /usr/local/bin/backup-crm.sh >> /var/log/crm-backup.log 2>&1
```

#### 5.2 Log Rotation
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/glomart-crm
```

```
/var/www/glomart-crm/logs/*.log {
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
```

#### 5.3 Basic Monitoring
```bash
# Create simple health check script
sudo nano /usr/local/bin/health-check.sh
```

```bash
#!/bin/bash
# Simple health check for Glomart CRM

SITE_URL="https://your-domain.com"
LOG_FILE="/var/log/crm-health.log"

# Check if site is responding
if curl -s --head $SITE_URL | head -n 1 | grep -q "200 OK"; then
    echo "$(date): Site is UP" >> $LOG_FILE
else
    echo "$(date): Site is DOWN - restarting services" >> $LOG_FILE
    sudo systemctl restart gunicorn
    sudo systemctl restart nginx
fi
```

```bash
# Make executable and add to crontab (every 5 minutes)
sudo chmod +x /usr/local/bin/health-check.sh
sudo crontab -e
# Add line: */5 * * * * /usr/local/bin/health-check.sh
```

## 🔒 Security Checklist

- [ ] Change default passwords for all accounts
- [ ] Configure firewall (UFW) with minimal open ports
- [ ] Set up SSH key authentication and disable password login
- [ ] Install fail2ban for intrusion prevention
- [ ] Regular security updates
- [ ] Database user with minimal privileges
- [ ] SSL certificate installed and configured
- [ ] Security headers configured in Nginx
- [ ] Django secret key properly secured
- [ ] Debug mode disabled in production

## 🚀 Deployment Commands Summary

```bash
# Quick deployment script
#!/bin/bash
cd /var/www/glomart-crm
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## 📊 Performance Optimization

### Database Optimization
```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_property_status ON properties_property(status);
CREATE INDEX idx_lead_assigned_to ON leads_lead(assigned_to_id);
CREATE INDEX idx_user_profile_user ON authentication_userprofile(user_id);
```

### Nginx Caching
```nginx
# Add to nginx configuration
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔧 Troubleshooting

### Common Issues:
1. **502 Bad Gateway**: Check Gunicorn socket permissions
2. **Static files not loading**: Verify STATIC_ROOT and collectstatic
3. **Database connection errors**: Check MariaDB credentials and permissions
4. **Permission denied**: Verify file ownership and permissions

### Log Locations:
- Nginx: `/var/log/nginx/error.log`
- Gunicorn: `journalctl -u gunicorn`
- Django: `/var/www/glomart-crm/logs/django.log`
- System: `/var/log/syslog`

## 📞 Support

For issues or questions about this deployment guide, check:
1. Django logs for application errors
2. Nginx logs for web server issues
3. System logs for general server problems
4. Database logs for data-related issues

Remember to test all configurations in a staging environment before applying to production!