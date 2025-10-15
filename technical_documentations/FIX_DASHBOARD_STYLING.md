# 🎨 Fix Dashboard Styling Issues

## Problem: CSS/JavaScript Not Loading
The dashboard is working but the modern styling isn't loading properly.

## Run These Commands on Production Server:

### Step 1: Check Static Files Configuration
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Check static files settings
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()
from django.conf import settings
print('STATIC_URL:', settings.STATIC_URL)
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATICFILES_DIRS:', settings.STATICFILES_DIRS)
"
```

### Step 2: Collect Static Files
```bash
# Collect all static files
python manage.py collectstatic --noinput

# Check if static files were created
ls -la staticfiles/
ls -la static/
```

### Step 3: Fix Static Files Permissions
```bash
# Fix ownership of static files
sudo chown -R www-data:www-data /var/www/glomart-crm/staticfiles/
sudo chown -R www-data:www-data /var/www/glomart-crm/static/

# Fix permissions
sudo chmod -R 755 /var/www/glomart-crm/staticfiles/
sudo chmod -R 755 /var/www/glomart-crm/static/
```

### Step 4: Check Nginx Configuration
```bash
# Check if nginx is serving static files correctly
sudo nano /etc/nginx/sites-available/glomart-crm

# Make sure it has these lines:
location /static/ {
    alias /var/www/glomart-crm/staticfiles/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /var/www/glomart-crm/media/;
}
```

### Step 5: Test Static Files Directly
```bash
# Test if CSS files are accessible
curl -I http://127.0.0.1:8000/static/css/dashboard.css
curl -I http://127.0.0.1:8000/static/js/dashboard.js

# Check through nginx (if configured)
curl -I https://sys.glomartrealestates.com/static/css/dashboard.css
```

### Step 6: Restart Services
```bash
# Restart both services
sudo systemctl restart glomart-crm
sudo systemctl reload nginx

# Check status
sudo systemctl status glomart-crm
sudo systemctl status nginx
```

### Step 7: Debug Template Issues
```bash
# Check if template is loading CSS properly
curl -s http://127.0.0.1:8000/dashboard/ | grep -E "(css|bootstrap|stylesheet)"
```

## Alternative: Inline CSS Fix
If static files continue to have issues, we can embed the CSS directly in the template:

```bash
# Edit the dashboard template to include inline CSS
nano authentication/templates/authentication/dashboard.html

# Add CSS directly in <style> tags in the <head> section
# This bypasses static file serving issues
```

## Expected Results:
- ✅ Static files should be collected successfully
- ✅ CSS/JS files should return HTTP 200 when accessed directly
- ✅ Dashboard should show modern styling with gradients and animations
- ✅ Responsive design should work on different screen sizes

Run these commands in order and let me know:
1. What the static files settings show
2. If collectstatic runs successfully
3. If you can access CSS files directly via curl