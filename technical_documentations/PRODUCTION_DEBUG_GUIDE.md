# 🔍 Production Server Debug Guide

## Step 1: Check Server Status
SSH to your server and run these commands:

```bash
ssh root@sys.glomartrealestates.com
cd /var/www/glomart-crm

# Check current git status
git status
git log --oneline -5

# Check if latest changes are pulled
git fetch origin main
git diff HEAD origin/main
```

## Step 2: Check Service Status
```bash
# Check service status
sudo systemctl status glomart-crm
sudo journalctl -u glomart-crm -n 50

# Check if process is running
ps aux | grep gunicorn
ps aux | grep glomart
```

## Step 3: Check Application Logs
```bash
# Check Django logs
tail -f /var/log/glomart-crm/django.log

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Step 4: Test Application Directly
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Test if Django can start
python manage.py check
python manage.py showmigrations

# Test database connection
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()
from django.db import connection
print('Database connection:', connection.ensure_connection())
"

# Test dashboard view
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()
from django.test import Client
client = Client()
response = client.get('/')
print('Home page status:', response.status_code)
"
```

## Step 5: Check File Permissions
```bash
# Check ownership
ls -la /var/www/glomart-crm/

# Fix permissions if needed
sudo chown -R www-data:www-data /var/www/glomart-crm/
sudo chmod -R 755 /var/www/glomart-crm/
```

## Step 6: Force Deploy Latest Changes
```bash
cd /var/www/glomart-crm

# Backup current version
sudo cp -r /var/www/glomart-crm /var/backups/glomart-crm-backup-$(date +%Y%m%d_%H%M%S)

# Force pull latest changes
git fetch origin main
git reset --hard origin/main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements-production.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Fix permissions
sudo chown -R www-data:www-data /var/www/glomart-crm/
sudo chmod -R 755 /var/www/glomart-crm/

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart glomart-crm
sudo systemctl reload nginx

# Check status
sudo systemctl status glomart-crm
curl -I http://127.0.0.1:8000/
```

## Step 7: Debug Specific Issues

### If Dashboard Shows Error:
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Test dashboard calculations
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from leads.models import Lead, LeadStatus
from properties.models import Property

print('Testing dashboard data...')
print('Total properties:', Property.objects.count())
print('Total leads:', Lead.objects.count())

# Test the fixed lead status query
active_leads = Lead.objects.filter(
    status__is_final=False,
    status__is_active=True
).count()
print('Active leads:', active_leads)
"
```

### If Service Won't Start:
```bash
# Check gunicorn directly
cd /var/www/glomart-crm
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 real_estate_crm.wsgi:application

# Check for syntax errors
python manage.py check --deploy
```

### If Database Issues:
```bash
# Check MariaDB connection
mysql -u glomart_crm_user -p glomart_crm
# Enter your database password

# Inside MySQL:
SHOW TABLES;
SELECT COUNT(*) FROM properties_property;
SELECT COUNT(*) FROM leads_lead;
EXIT;
```

## Common Issues & Solutions

### Issue 1: Old Code Still Running
**Solution:** Force git pull and restart
```bash
git reset --hard origin/main
sudo systemctl restart glomart-crm
```

### Issue 2: Permission Issues
**Solution:** Fix ownership
```bash
sudo chown -R www-data:www-data /var/www/glomart-crm/
```

### Issue 3: Service Using Wrong Settings
**Solution:** Check service file
```bash
sudo nano /etc/systemd/system/glomart-crm.service
# Ensure it uses production settings
sudo systemctl daemon-reload
sudo systemctl restart glomart-crm
```

### Issue 4: Database Connection Error
**Solution:** Check database settings
```bash
# Test database connection
python manage.py dbshell
```

## Next Steps
After running these commands, please share:
1. Output of `systemctl status glomart-crm`
2. Last 20 lines of `journalctl -u glomart-crm -n 20`
3. Any error messages you see
4. Current git status with `git log --oneline -5`

This will help identify exactly what's preventing the updates from showing in production.