# 🚨 URGENT: Database Connection Fix

## Problem Identified:
Your Django app is trying to connect to MySQL with user 'root' but the password is wrong.

## Fix Database Connection (Run on your server):

### Step 1: Check Current Database Settings
```bash
cd /var/www/glomart-crm
grep -A 10 "DATABASES" real_estate_crm/settings.py
```

### Step 2: Test MySQL Connection Manually
```bash
# Try to connect to MySQL as root
mysql -u root -p

# If that doesn't work, try with your actual database user
mysql -u glomart_crm_user -p glomart_crm
```

### Step 3: Fix Database Configuration
You have two options:

#### Option A: Update Django Settings (Recommended)
```bash
cd /var/www/glomart-crm
nano real_estate_crm/settings.py
```

**Change the DATABASES section to:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'glomart_crm',  # or your actual database name
        'USER': 'glomart_crm_user',  # your actual database user
        'PASSWORD': 'your_actual_db_password',  # your actual password
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

#### Option B: Reset MySQL Root Password (If needed)
```bash
# Stop MySQL
sudo systemctl stop mysql

# Start in safe mode
sudo mysqld_safe --skip-grant-tables &

# Connect and reset password
mysql -u root
USE mysql;
UPDATE user SET authentication_string=PASSWORD('your_new_password') WHERE User='root';
FLUSH PRIVILEGES;
EXIT;

# Restart MySQL normally
sudo systemctl restart mysql
```

### Step 4: Test Database Connection
```bash
cd /var/www/glomart-crm
source venv/bin/activate

# Test Django database connection
python manage.py dbshell
# If this connects successfully, type: \q to quit
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

## Quick Fix Commands (Run these in order):

```bash
# 1. Check what database exists
mysql -u root -p -e "SHOW DATABASES;"

# 2. Check what users exist
mysql -u root -p -e "SELECT User, Host FROM mysql.user;"

# 3. Edit Django settings
cd /var/www/glomart-crm
nano real_estate_crm/settings.py
# Update the DATABASE settings with correct credentials

# 4. Test Django connection
source venv/bin/activate
python manage.py check

# 5. Restart service
sudo systemctl restart glomart-crm
```

## Expected Result:
After fixing the database connection, your dashboard should load properly without the MySQL access denied error.