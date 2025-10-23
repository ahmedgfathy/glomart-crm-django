#!/usr/bin/env python3
"""
Production MariaDB Connection Fix
This script creates the correct settings and commands for your production environment.
"""
import os

def create_production_mariadb_commands():
    """Create MariaDB commands for production server"""
    
    commands = """
# =========================================
# Production MariaDB Connection Fix Guide
# =========================================

# Step 1: Connect to your production server
ssh root@sys.glomartrealestates.com

# Step 2: Check MariaDB service status
sudo systemctl status mariadb

# Step 3: Test root connection with your actual password
mysql -u root -p
# Enter password: ZeroCall20!@HH##1655&&

# Step 4: Once connected to MariaDB, run these SQL commands:
# ========================================================

-- Check if database exists
SHOW DATABASES LIKE 'django_db_glomart_rs';

-- If database doesn't exist, create it
CREATE DATABASE IF NOT EXISTS django_db_glomart_rs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create dedicated Django user (more secure than using root)
CREATE USER IF NOT EXISTS 'django_prod'@'localhost' IDENTIFIED BY 'DjangoProd2024!Secure#';

-- Grant all privileges on the Django database
GRANT ALL PRIVILEGES ON django_db_glomart_rs.* TO 'django_prod'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify the user was created
SELECT User, Host FROM mysql.user WHERE User = 'django_prod';

-- Test the database exists
USE django_db_glomart_rs;
SHOW TABLES;

-- Exit MariaDB
EXIT;

# Step 5: Test the new user connection
mysql -u django_prod -p django_db_glomart_rs
# Enter password: DjangoProd2024!Secure#

# Step 6: If you prefer to keep using root user, fix root permissions:
# ====================================================================
mysql -u root -p
# Run: GRANT ALL PRIVILEGES ON django_db_glomart_rs.* TO 'root'@'localhost';
# Run: FLUSH PRIVILEGES;
# Run: EXIT;

# Step 7: Update Django settings (see update_production_settings.py)

# Step 8: Test Django connection
cd /var/www/glomart-crm
source venv/bin/activate
python manage.py check --database default

# Step 9: Restart Django service
sudo systemctl restart glomart-crm
sudo systemctl status glomart-crm
"""
    
    with open('production_mariadb_fix.txt', 'w') as f:
        f.write(commands)
    
    print("✅ Created production_mariadb_fix.txt")

def create_production_settings_update():
    """Create settings update for production"""
    
    # Option 1: Using new dedicated user (recommended)
    settings_new_user = """
# ==========================================
# OPTION 1: Use dedicated Django user (RECOMMENDED)
# ==========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'USER': 'django_prod',
        'PASSWORD': 'DjangoProd2024!Secure#',
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
"""

    # Option 2: Fix root user (if you want to keep using root)
    settings_root_user = """
# ==========================================
# OPTION 2: Fix root user configuration  
# ==========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'USER': 'root',
        'PASSWORD': 'ZeroCall20!@HH##1655&&',  # Your actual production password
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
"""
    
    with open('update_production_settings.py', 'w') as f:
        f.write("# Production Database Settings Update\n")
        f.write("# Choose one of these options:\n\n")
        f.write(settings_new_user)
        f.write("\n\n")
        f.write(settings_root_user)
    
    print("✅ Created update_production_settings.py")

def create_quick_root_fix():
    """Create a quick fix script that just updates the password"""
    
    script_content = '''#!/usr/bin/env python3
"""
Quick fix: Update settings.py with correct root password
"""
import os
import re

def update_settings_password():
    settings_path = '/var/www/glomart-crm/real_estate_crm/settings.py'
    
    if not os.path.exists(settings_path):
        settings_path = 'real_estate_crm/settings.py'  # Local development path
    
    try:
        with open(settings_path, 'r') as f:
            content = f.read()
        
        # Update the password in DATABASES configuration
        # Look for the password line and replace it
        updated_content = re.sub(
            r"'PASSWORD': '[^']*'",
            "'PASSWORD': 'ZeroCall20!@HH##1655&&'",
            content
        )
        
        with open(settings_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated password in {settings_path}")
        print("✅ Settings now use correct production password")
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")
        print("Please update manually:")
        print("Change 'PASSWORD': 'zerocall' to 'PASSWORD': 'ZeroCall20!@HH##1655&&'")

if __name__ == "__main__":
    update_settings_password()
'''
    
    with open('quick_password_fix.py', 'w') as f:
        f.write(script_content)
    
    os.chmod('quick_password_fix.py', 0o755)
    print("✅ Created quick_password_fix.py")

def create_django_test_script():
    """Create script to test Django database connection"""
    
    test_script = '''#!/usr/bin/env python3
"""
Test Django database connection on production server
Run this on your production server: /var/www/glomart-crm/
"""
import os
import sys
import django
from pathlib import Path

def test_django_db():
    # Set up Django environment
    project_root = Path('/var/www/glomart-crm')
    if not project_root.exists():
        project_root = Path('.')  # Local development
    
    sys.path.insert(0, str(project_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
    
    try:
        print("🔧 Setting up Django...")
        django.setup()
        
        from django.db import connection
        
        print("🔗 Testing database connection...")
        
        # Test basic connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✅ Basic connection test: {result}")
        
        # Test Django models
        from django.contrib.auth.models import User
        user_count = User.objects.count()
        print(f"✅ User model test: {user_count} users found")
        
        # Test database info
        db_info = connection.get_connection_params()
        print(f"✅ Database: {db_info.get('db', 'N/A')}")
        print(f"✅ User: {db_info.get('user', 'N/A')}")
        print(f"✅ Host: {db_info.get('host', 'N/A')}")
        
        print("\\n🎉 All database tests passed!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        print("\\n🔧 Debug information:")
        print("1. Check MariaDB is running: sudo systemctl status mariadb")
        print("2. Verify database exists: mysql -u root -p -e 'SHOW DATABASES;'")
        print("3. Check user permissions: mysql -u root -p -e 'SHOW GRANTS FOR \\'root\\'@\\'localhost\\';'")
        
        sys.exit(1)

if __name__ == "__main__":
    test_django_db()
'''
    
    with open('test_production_db.py', 'w') as f:
        f.write(test_script)
    
    os.chmod('test_production_db.py', 0o755)
    print("✅ Created test_production_db.py")

if __name__ == "__main__":
    print("🔧 Production MariaDB Fix Generator")
    print("=" * 50)
    
    create_production_mariadb_commands()
    create_production_settings_update()
    create_quick_root_fix()
    create_django_test_script()
    
    print("\n📋 IMMEDIATE FIX - Choose one:")
    print("=" * 30)
    print("OPTION A (Quick): Run 'python3 quick_password_fix.py' to fix the password")
    print("OPTION B (Secure): Follow production_mariadb_fix.txt to create dedicated user")
    
    print("\n📋 After fixing settings:")
    print("1. Run: python3 test_production_db.py")  
    print("2. SSH to server and restart: sudo systemctl restart glomart-crm")
    print("3. Check: https://sys.glomartrealestates.com/dashboard/")