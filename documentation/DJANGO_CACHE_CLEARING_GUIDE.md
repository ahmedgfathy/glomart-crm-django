# Django Cache Clearing Methods

Django has several types of caches that might be preventing your sidebar changes from showing up. Here are all the ways to clear them:

## 1. Django Template Cache (Most Common Issue)

### Method 1: Restart Django Application
```bash
# On your production server
systemctl restart glomart-crm
# OR if using different process manager
sudo service gunicorn restart
# OR kill and restart manually
pkill -f gunicorn
```

### Method 2: Clear Template Cache via Django Shell
```bash
# On production server
cd /var/www/glomart-crm
source venv/bin/activate
python manage.py shell

# In Django shell:
from django.core.cache import cache
cache.clear()
print("Template cache cleared!")
exit()
```

### Method 3: Disable Template Caching (Temporary)
```python
# In settings.py - add this temporarily for debugging
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [...],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [...],
            'debug': True,  # Force reload templates
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]
```

## 2. Browser Cache Clearing

### Complete Browser Cache Clear
- **Chrome/Edge**: Ctrl+Shift+Delete → Select "All time" → Check all boxes → Clear
- **Firefox**: Ctrl+Shift+Delete → Select "Everything" → Check all boxes → Clear
- **Safari**: Cmd+Option+E → Develop menu → Empty Caches

### Force Hard Refresh
- **Windows**: Ctrl+F5 or Ctrl+Shift+R
- **Mac**: Cmd+Shift+R or Cmd+Option+R
- **Alternative**: Open in Incognito/Private mode

## 3. Django Application Cache

### Clear All Django Caches
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Method 1: Management command (if available)
python manage.py clear_cache

# Method 2: Via Django shell
python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('All caches cleared!')
"
```

### Clear Specific Cache Keys
```python
# If you know specific cache keys
from django.core.cache import cache

# Clear template fragments
cache.delete_many(['template_fragment_*'])

# Clear session cache
cache.delete_many(['session_*'])

# Clear view cache
cache.delete_many(['view_cache_*'])
```

## 4. Static Files Cache

### Collect Static Files Again
```bash
cd /var/www/glomart-crm
source venv/bin/activate
python manage.py collectstatic --clear --noinput
```

### Clear Static Files and Re-collect
```bash
# Remove collected static files
rm -rf /var/www/glomart-crm/staticfiles/*
# Re-collect
python manage.py collectstatic --noinput
```

## 5. Nginx Cache (If Configured)

### Clear Nginx Cache
```bash
# If nginx is caching (check nginx config)
sudo nginx -s reload

# Or clear nginx cache directory (if configured)
sudo rm -rf /var/cache/nginx/*
sudo systemctl reload nginx
```

## 6. Database Query Cache

### Clear Django ORM Cache
```python
# In Django shell
from django.db import connection
connection.queries_log.clear()

# Reset database connections
from django.db import connections
connections.close_all()
```

## 7. Python Bytecode Cache

### Clear Python Cache Files
```bash
cd /var/www/glomart-crm
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## Complete Cache Clear Script

Here's a comprehensive script to clear all caches:

```bash
#!/bin/bash
# Complete Django cache clearing script

cd /var/www/glomart-crm

echo "🧹 Starting complete cache clear..."

# 1. Clear Django application cache
source venv/bin/activate
python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('✅ Django cache cleared')
"

# 2. Clear Python bytecode
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Python bytecode cleared"

# 3. Clear and re-collect static files
python manage.py collectstatic --clear --noinput
echo "✅ Static files cleared and re-collected"

# 4. Restart application
systemctl restart glomart-crm
echo "✅ Application restarted"

# 5. Reload nginx
systemctl reload nginx 2>/dev/null
echo "✅ Nginx reloaded"

echo "🎉 All caches cleared! Please hard refresh your browser."
```

## Quick Fix for Sidebar Issue

For your specific sidebar template issue, try this sequence:

```bash
# 1. SSH to your server
ssh root@sys.glomartrealestates.com

# 2. Navigate to project
cd /var/www/glomart-crm

# 3. Pull latest changes
git fetch origin && git reset --hard origin/main

# 4. Clear Django cache
source venv/bin/activate
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')"

# 5. Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 6. Restart service
systemctl restart glomart-crm

# 7. Check service status
systemctl status glomart-crm --no-pager
```

After running these commands, force refresh your browser (Ctrl+F5) and the sidebar changes should be visible!