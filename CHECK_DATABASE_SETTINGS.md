# 🔧 URGENT: Check and Fix Database Settings

## Run These Commands on Production Server:

### Step 1: Check Current Database Settings
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Proper way to check Django settings
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()
from django.conf import settings
print('Current DB settings:')
print('NAME:', settings.DATABASES['default']['NAME'])
print('USER:', settings.DATABASES['default']['USER'])
print('PASSWORD:', settings.DATABASES['default']['PASSWORD'])
print('HOST:', settings.DATABASES['default']['HOST'])
"
```

### Step 2: If Password Is Still Wrong, Fix It Manually
```bash
# Edit the settings file directly
nano real_estate_crm/settings.py

# Find the DATABASES section and make sure it looks like this:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'ZeroCall20!@HH##1655&&',  # ← This must be correct
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Save with: Ctrl+X, then Y, then Enter
```

### Step 3: Test Database Connection Directly
```bash
# Test MySQL connection with correct password
mysql -u root -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SELECT COUNT(*) as total_properties FROM properties_property;"
```

### Step 4: Test Django Connection
```bash
cd /var/www/glomart-crm
source venv/bin/activate

python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT COUNT(*) FROM properties_property')
    count = cursor.fetchone()[0]
    print(f'✅ Database connection successful! Properties count: {count}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### Step 5: Restart Service
```bash
sudo systemctl restart glomart-crm
sudo systemctl status glomart-crm --no-pager
```

### Step 6: Test Dashboard
```bash
curl -I http://127.0.0.1:8000/dashboard/
```

## Expected Results:
- ✅ Step 1 should show the correct password
- ✅ Step 3 should show a number (like 3229 properties)
- ✅ Step 4 should show "Database connection successful!"
- ✅ Step 5 should show "Active: active (running)"
- ✅ Step 6 should show "HTTP/1.1 302 Found" (redirect to login)

Run these in order and share the outputs!