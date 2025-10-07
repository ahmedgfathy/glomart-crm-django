# 🔍 STEP-BY-STEP Dashboard Error Debug

## Current Issue: Dashboard still showing error after fixes

The screenshot shows you're still getting an error on the dashboard. Let's debug this systematically.

## Run These Commands on Your Production Server:

### Step 1: Check Current Service Status
```bash
cd /var/www/glomart-crm
sudo systemctl status glomart-crm --no-pager
```

### Step 2: Check What Code Version Is Actually Running
```bash
cd /var/www/glomart-crm
git log --oneline -3
git status
```

### Step 3: Check If Our Dashboard Fix Is Present
```bash
cd /var/www/glomart-crm
# Check if the fixed dashboard view exists
grep -n "status__is_final=False" authentication/views.py
```

### Step 4: Test Dashboard View Directly on Production
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Test the dashboard calculations on production
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from leads.models import Lead, LeadStatus
from properties.models import Property

print('Production data check:')
print('Total properties:', Property.objects.count())
print('Total leads:', Lead.objects.count())

# Test our fixed query
try:
    active_leads = Lead.objects.filter(
        status__is_final=False,
        status__is_active=True
    ).count()
    print('✅ Active leads query works:', active_leads)
except Exception as e:
    print('❌ Active leads query failed:', str(e))

# Test if dashboard view works
try:
    from authentication.views import dashboard_view
    print('✅ Dashboard view can be imported')
except Exception as e:
    print('❌ Dashboard view import failed:', str(e))
"
```

### Step 5: If Service Is Still Failing, Check Detailed Logs
```bash
# Get more detailed error logs
sudo journalctl -u glomart-crm -n 50 --no-pager

# Check if gunicorn is actually running
ps aux | grep gunicorn | grep -v grep
```

### Step 6: Force Restart Everything
```bash
cd /var/www/glomart-crm

# Pull latest code again
git fetch origin main
git reset --hard origin/main

# Fix permissions again
sudo chown -R www-data:www-data /var/www/glomart-crm/
sudo chmod -R 755 /var/www/glomart-crm/

# Kill any existing gunicorn processes
sudo pkill -f gunicorn

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart glomart-crm
sudo systemctl status glomart-crm --no-pager

# Test response
curl -v http://127.0.0.1:8000/dashboard/
```

### Step 7: If Still Not Working, Try Manual Start
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Try starting gunicorn manually to see exact error
gunicorn --bind 127.0.0.1:8000 --timeout 30 real_estate_crm.wsgi:application

# If that works, press Ctrl+C and restart service
sudo systemctl restart glomart-crm
```

## Expected Outputs:

✅ **Service should show**: `Active: active (running)`
✅ **Git log should show**: The latest commits with dashboard fixes
✅ **Dashboard query test should show**: `Active leads query works: X`
✅ **curl should return**: `HTTP/1.1 302 Found` (redirect to login)

## Most Likely Issues:

1. **Code not updated**: Server still has old dashboard code
2. **Service not actually running**: Despite status showing "running"
3. **Database connection issue**: Can't connect to MariaDB
4. **Permission issues**: Still can't write logs or access files

Run these commands in order and share the outputs, especially:
- `systemctl status glomart-crm`
- The output of the Python test script
- Any error messages you see

This will help identify exactly what's preventing the dashboard from working.