# 🔧 Fix Database Password Mismatch

## Problem:
Django settings show password: `zerocall`
Actual MySQL root password: `ZeroCall20!@HH##1655&&`

## Fix on Production Server:

### Step 1: Update Django Settings
```bash
cd /var/www/glomart-crm
nano real_estate_crm/settings.py
```

**Find the DATABASES section and update the password:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'ZeroCall20!@HH##1655&&',  # <-- Update this line
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

### Step 2: Test MySQL Connection
```bash
# Test with the correct password
mysql -u root -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SELECT COUNT(*) FROM properties_property;"
```

### Step 3: Test Django Connection
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Test Django database connection
python manage.py check
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()
from django.db import connection
cursor = connection.cursor()
print('✅ Database connection successful!')
"
```

### Step 4: Restart Service
```bash
sudo systemctl restart glomart-crm
sudo systemctl status glomart-crm --no-pager
```

### Step 5: Test Dashboard
```bash
curl -I http://127.0.0.1:8000/dashboard/
```

## Expected Result:
- Django should connect to MySQL successfully
- Dashboard should load without database errors
- You should see HTTP 302 (redirect to login) or HTTP 200

## Alternative: Use Environment Variables (More Secure)
If you want to be more secure, create a `.env` file:

```bash
cd /var/www/glomart-crm
nano .env
```

Add:
```
DB_PASSWORD=ZeroCall20!@HH##1655&&
```

Then update settings.py:
```python
import os
from pathlib import Path

# Load environment variables
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': os.environ.get('DB_PASSWORD', 'zerocall'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

This way the password won't be visible in the code.