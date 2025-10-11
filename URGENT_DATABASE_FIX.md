# 🚨 URGENT: Fix Database Connection Error

## Problem: 
Django can't connect to MySQL: `(1045, "Access denied for user 'root'@'localhost' (using password: YES)")`

## Root Cause:
Either the MySQL root password is wrong, or the database user doesn't exist, or MySQL is not running.

## IMMEDIATE FIX - Run these commands on your server:

### Step 1: Check MySQL Service Status
```bash
systemctl status mysql
# or
systemctl status mariadb
```

### Step 2: Test MySQL Connection Manually
```bash
# Test with the password Django is trying to use
mysql -u root -p'ZeroCall20!@HH##1655&&'

# If that fails, try without password
mysql -u root

# If that fails, try with common passwords
mysql -u root -p'zerocall'
mysql -u root -p'root'
mysql -u root -p''
```

### Step 3A: If MySQL Connection Works - Check Database
```bash
mysql -u root -p'ZeroCall20!@HH##1655&&' -e "SHOW DATABASES;"
mysql -u root -p'ZeroCall20!@HH##1655&&' -e "USE django_db_glomart_rs; SHOW TABLES;"
```

### Step 3B: If MySQL Connection Fails - Reset Root Password
```bash
# Stop MySQL
systemctl stop mysql

# Start in safe mode
mysqld_safe --skip-grant-tables --skip-networking &

# Connect and reset password
mysql -u root
```

```sql
USE mysql;
UPDATE user SET authentication_string=PASSWORD('ZeroCall20!@HH##1655&&') WHERE User='root';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# Kill safe mode and restart normally
pkill mysqld_safe
pkill mysqld
systemctl start mysql
```

### Step 4: Verify Database Settings in Django
```bash
cd /var/www/glomart-crm
grep -A 10 "DATABASES" real_estate_crm/settings.py
```

Should show:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'USER': 'root',
        'PASSWORD': 'ZeroCall20!@HH##1655&&',
        'HOST': 'localhost',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

### Step 5: Test Django Database Connection
```bash
cd /var/www/glomart-crm
source venv/bin/activate
python manage.py dbshell
# This should connect without errors
# Type: \q to exit
```

### Step 6: Restart Django Service
```bash
systemctl restart glomart-crm
systemctl status glomart-crm --no-pager
```

## Alternative Quick Fix - Use SQLite Temporarily
If MySQL is too problematic, temporarily switch to SQLite:

```bash
cd /var/www/glomart-crm
cp real_estate_crm/settings.py real_estate_crm/settings.py.backup

# Create temporary SQLite settings
cat > /tmp/sqlite_settings.py << 'EOF'
# Replace DATABASES section with SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
EOF

# Replace database section in settings.py
sed -i '/^DATABASES = {/,/^}/c\
DATABASES = {\
    "default": {\
        "ENGINE": "django.db.backends.sqlite3",\
        "NAME": BASE_DIR / "db.sqlite3",\
    }\
}' real_estate_crm/settings.py

# Migrate database
source venv/bin/activate
python manage.py migrate

# Restart service
systemctl restart glomart-crm
```

## Most Likely Solutions:

### Solution 1: Wrong MySQL Password
The password `ZeroCall20!@HH##1655&&` might not be set for MySQL root user.

### Solution 2: MySQL Not Running
Check if MySQL/MariaDB service is running.

### Solution 3: Database Doesn't Exist
The database `django_db_glomart_rs` might not exist.

Run these commands to diagnose and fix the issue immediately!