# 🚀 Production Deployment Fix Guide

## Issues Found

1. **Service Configuration Mismatch**: GitHub Actions restarts `glomart-crm` but update script restarts `gunicorn`
2. **Settings Module Error**: Update script references non-existent `settings_production`
3. **DEBUG Mode**: Production running with DEBUG=True
4. **Inconsistent Service Names**: Multiple service references

## Fix Steps

### 1. Fix Service Configuration

**On your production server, run these commands:**

```bash
# Check current service status
sudo systemctl status glomart-crm
sudo systemctl status gunicorn

# If both exist, disable the old gunicorn service
sudo systemctl stop gunicorn
sudo systemctl disable gunicorn

# Make sure glomart-crm service is properly configured
sudo systemctl enable glomart-crm
sudo systemctl start glomart-crm
```

### 2. Update GitHub Actions Workflow

The workflow looks correct, but make sure it's using the right service name.

### 3. Fix Production Settings

**Create proper production settings:**

```bash
cd /var/www/glomart-crm/real_estate_crm
cp settings.py settings_production.py
```

Then edit `settings_production.py`:

```python
# Production settings
DEBUG = False
ALLOWED_HOSTS = ['sys.glomartrealestates.com', '5.180.148.92']

# Use environment variables for sensitive data
import os
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-production-secret-key')

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'glomart_crm'),
        'USER': os.environ.get('DB_USER', 'your_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}

# Static files
STATIC_ROOT = '/var/www/glomart-crm/staticfiles'
MEDIA_ROOT = '/var/www/glomart-crm/media'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 4. Update Service File

**Make sure your service file uses production settings:**

```bash
sudo nano /etc/systemd/system/glomart-crm.service
```

Update the ExecStart line:

```ini
ExecStart=/bin/bash -c 'cd /var/www/glomart-crm && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production && exec gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 30 --keep-alive 2 --max-requests 1000 --max-requests-jitter 50 --preload real_estate_crm.wsgi:application'
```

### 5. Test Deployment

**Run these commands to test:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Restart the service
sudo systemctl restart glomart-crm

# Check status
sudo systemctl status glomart-crm

# Check if it's serving the right content
curl -I http://127.0.0.1:8000/

# Check logs
sudo journalctl -u glomart-crm -f
```

### 6. Verify GitHub Actions Deployment

**SSH to your server and check:**

```bash
# Go to app directory
cd /var/www/glomart-crm

# Check current commit
git log --oneline -5

# Check if files are actually updated
ls -la

# Force pull latest changes
git fetch origin main
git reset --hard origin/main

# Restart services manually
sudo systemctl restart glomart-crm
sudo systemctl reload nginx
```

### 7. Environment Variables Setup

**Create a production environment file:**

```bash
cd /var/www/glomart-crm
sudo nano .env.production
```

Add your production variables:

```bash
SECRET_KEY=your-production-secret-key
DB_NAME=glomart_crm
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
DEBUG=False
```

### 8. Update Deployment Scripts

**Fix the update-app.sh script to use correct settings:**

Change this line:
```bash
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
```

## Debugging Commands

If deployment still fails, use these debugging commands:

```bash
# Check service logs
sudo journalctl -u glomart-crm -n 50

# Check nginx logs  
sudo tail -f /var/log/nginx/error.log

# Check if process is running
ps aux | grep gunicorn

# Test direct gunicorn start
cd /var/www/glomart-crm
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 real_estate_crm.wsgi:application

# Check file permissions
ls -la /var/www/glomart-crm/

# Verify git status
git status
git remote -v
```

## Quick Fix Commands

**Run these on your production server NOW:**

```bash
# 1. Go to app directory
cd /var/www/glomart-crm

# 2. Force update code
git fetch origin main
git reset --hard origin/main

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements-production.txt

# 5. Run migrations
python manage.py migrate

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Fix permissions
sudo chown -R www-data:www-data /var/www/glomart-crm/
sudo chmod -R 755 /var/www/glomart-crm/

# 8. Restart services
sudo systemctl daemon-reload
sudo systemctl restart glomart-crm
sudo systemctl reload nginx

# 9. Check status
sudo systemctl status glomart-crm
curl -I http://127.0.0.1:8000/
```

After running these commands, your production should reflect the latest changes!